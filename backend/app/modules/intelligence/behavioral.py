from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.entities import BehaviorProfile, utc_now


class BehavioralAnalyticsEngine:
    async def get_or_create_profile(
        self,
        db: AsyncSession,
        organization_id: str,
        actor_pseudonym: str
    ) -> BehaviorProfile:
        query = select(BehaviorProfile).where(
            BehaviorProfile.organization_id == organization_id,
            BehaviorProfile.actor_pseudonym == actor_pseudonym
        )
        res = await db.execute(query)
        profile = res.scalar_one_or_none()

        if not profile:
            # Cold-start baseline defaults
            baseline = {
                "known_devices": [],
                "typical_hours": [9, 10, 11, 12, 13, 14, 15, 16, 17, 18],  # 9 AM - 6 PM
                "avg_requests_per_min": 15.0,
                "std_requests_per_min": 5.0,
                "total_events_observed": 0,
                "last_active": None,
                "failed_login_count_history": 0
            }
            profile = BehaviorProfile(
                organization_id=organization_id,
                actor_pseudonym=actor_pseudonym,
                baseline_features=baseline,
                recent_activity=[]
            )
            db.add(profile)
            await db.commit()
            await db.refresh(profile)

        return profile

    def compute_deviations(
        self,
        profile: BehaviorProfile,
        event_meta: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compares new activity against historical baseline and produces
        behavioral deviation features and explainable deviation score (0-100).
        """
        baseline = profile.baseline_features or {}
        known_devices = set(baseline.get("known_devices", []))
        typical_hours = set(baseline.get("typical_hours", [9, 10, 11, 12, 13, 14, 15, 16, 17, 18]))
        avg_rate = float(baseline.get("avg_requests_per_min", 15.0))
        std_rate = max(1.0, float(baseline.get("std_requests_per_min", 5.0)))

        # 1. Device Novelty
        device_hash = event_meta.get("device", {}).get("device_hash")
        device_novelty = 0.0
        if device_hash:
            if device_hash not in known_devices and len(known_devices) > 0:
                device_novelty = 1.0  # Novel device
            elif len(known_devices) == 0:
                device_novelty = 0.3  # Cold start bootstrap

        # 2. Time-of-Day Deviation
        now_utc = utc_now()
        current_hour = now_utc.hour
        # Distance from typical working hours
        if current_hour in typical_hours:
            hour_deviation = 0.0
        else:
            # Find minimum distance to any typical hour
            min_dist = min(abs(current_hour - h) for h in typical_hours)
            hour_deviation = min(1.0, min_dist / 6.0)

        # 3. Rate Deviation (Z-Score)
        current_rate = float(event_meta.get("metrics", {}).get("requests_per_minute", avg_rate))
        z_score = max(0.0, (current_rate - avg_rate) / std_rate)
        rate_deviation = min(1.0, z_score / 4.0)

        # 4. Failed Login Penalty
        failed_logins = int(event_meta.get("metrics", {}).get("failed_logins_5m", 0))
        failed_penalty = min(1.0, failed_logins / 5.0)

        # Combined Behavioral Deviation Score (0 - 100)
        weighted_dev = (
            (device_novelty * 0.35) +
            (hour_deviation * 0.25) +
            (rate_deviation * 0.20) +
            (failed_penalty * 0.20)
        )
        deviation_score = round(weighted_dev * 100.0, 1)

        deviation_reasons = []
        if device_novelty >= 0.8:
            deviation_reasons.append("Authentication from previously unobserved device")
        if hour_deviation >= 0.4:
            deviation_reasons.append(f"Activity outside typical active schedule (Hour {current_hour}:00 UTC)")
        if rate_deviation >= 0.5:
            deviation_reasons.append(f"Request velocity {current_rate:.1f} req/min exceeds baseline ({avg_rate:.1f} avg)")
        if failed_penalty >= 0.4:
            deviation_reasons.append(f"Cluster of {failed_logins} failed login attempts in 5-minute window")

        return {
            "deviation_score": deviation_score,
            "device_novelty": device_novelty,
            "time_of_day_deviation": round(hour_deviation, 3),
            "rate_deviation_z": round(z_score, 2),
            "deviation_reasons": deviation_reasons
        }

    async def update_baseline(
        self,
        db: AsyncSession,
        profile: BehaviorProfile,
        event_meta: Dict[str, Any]
    ):
        """Gradually adapts rolling baseline with new observation."""
        baseline = dict(profile.baseline_features or {})
        total_obs = baseline.get("total_events_observed", 0) + 1
        baseline["total_events_observed"] = total_obs

        # Update known devices
        device_hash = event_meta.get("device", {}).get("device_hash")
        if device_hash:
            devices = list(baseline.get("known_devices", []))
            if device_hash not in devices:
                devices.append(device_hash)
                # Keep max 5 most recent devices
                baseline["known_devices"] = devices[-5:]

        # Update rolling request rate (exponential moving average)
        req_rate = float(event_meta.get("metrics", {}).get("requests_per_minute", 15.0))
        old_avg = float(baseline.get("avg_requests_per_min", 15.0))
        alpha = 0.05  # Slow rolling adaptation
        baseline["avg_requests_per_min"] = round(old_avg * (1 - alpha) + req_rate * alpha, 2)
        baseline["last_active"] = utc_now().isoformat()

        profile.baseline_features = baseline
        await db.commit()


behavioral_engine = BehavioralAnalyticsEngine()
