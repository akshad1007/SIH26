import pandas as pd
from typing import Tuple, Dict, Any, Optional


class WatchlistDatabase:
    """
    Local High-Speed Watchlist / Whitelist Database for Border Security Operations.
    Implements Sub-millisecond offline matching for:
      - Authorized Personnel (Border Patrol Rosters / ArcFace Re-ID)
      - Authorized Patrol Vehicles (QRT Gypsies / Border Logistics ANPR)
    Enables Step 8 Alert Decision:
      - MATCH FOUND -> Suppress False Alarm, Log Event, Green UI Tag
      - NO MATCH -> Trigger Urgent Alarm, Red Siren Alert, Control Room Dispatch
    """
    def __init__(self):
        # Whitelisted Authorized Personnel (as shown in SIH technical flowchart)
        self.personnel = [
            {
                "personnel_id": "SSB-4587",
                "name": "Constable R. Singh",
                "rank": "Constable",
                "unit": "42nd Battalion SSB",
                "assigned_sector": "Sector A & B Patrol",
                "status": "AUTHORIZED",
                "simulated_track_ids": [1, 2]  # Designated tracks for authorized demo
            },
            {
                "personnel_id": "SSB-3120",
                "name": "Head Constable S. Yadav",
                "rank": "Head Constable",
                "unit": "BOP Sector Charlie",
                "assigned_sector": "Sector B Perimeter",
                "status": "AUTHORIZED",
                "simulated_track_ids": [7]
            },
            {
                "personnel_id": "SSB-1044",
                "name": "Inspector A. Sharma",
                "rank": "Inspector (Duty Officer)",
                "unit": "HQ Security Division",
                "assigned_sector": "All Sectors",
                "status": "AUTHORIZED",
                "simulated_track_ids": [14]
            }
        ]

        # Whitelisted Authorized Vehicles (ANPR plates)
        self.vehicles = [
            {
                "plate_number": "K433ZR",
                "vehicle_type": "QRT Gypsy / Patrol SUV",
                "unit": "SSB Quick Reaction Team (QRT-01)",
                "driver": "Constable D. Verma",
                "status": "AUTHORIZED"
            },
            {
                "plate_number": "MH12AB1234",
                "vehicle_type": "Sector Recon Van",
                "unit": "42nd Battalion Logistics",
                "driver": "Havildar P. Joshi",
                "status": "AUTHORIZED"
            },
            {
                "plate_number": "DL1CAA1111",
                "vehicle_type": "SSB Command Ambulance",
                "unit": "Medical Detachment BOP 4",
                "driver": "Constable N. Rao",
                "status": "AUTHORIZED"
            }
        ]

    def verify_person(self, track_id: int) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Queries watchlist for authorized person match.
        Returns (is_match, personnel_record).
        """
        for person in self.personnel:
            if track_id in person["simulated_track_ids"]:
                return True, person
        return False, None

    def verify_vehicle(self, plate_text: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Queries watchlist for authorized vehicle plate match.
        Returns (is_match, vehicle_record).
        """
        if not plate_text or plate_text in ["-", "PLATE_UNREADABLE"]:
            return False, None

        cleaned_input = plate_text.upper().replace(" ", "").replace("-", "")
        for veh in self.vehicles:
            cleaned_target = veh["plate_number"].upper().replace(" ", "").replace("-", "")
            if cleaned_input == cleaned_target:
                return True, veh
        return False, None

    def get_personnel_dataframe(self) -> pd.DataFrame:
        """Returns personnel watchlist as DataFrame."""
        return pd.DataFrame([
            {
                "Service ID": p["personnel_id"],
                "Name": p["name"],
                "Rank": p["rank"],
                "Unit": p["unit"],
                "Sector": p["assigned_sector"],
                "Status": p["status"]
            }
            for p in self.personnel
        ])

    def get_vehicles_dataframe(self) -> pd.DataFrame:
        """Returns vehicle watchlist as DataFrame."""
        return pd.DataFrame([
            {
                "Plate Number": v["plate_number"],
                "Vehicle Type": v["vehicle_type"],
                "Unit": v["unit"],
                "Driver / Crew": v["driver"],
                "Status": v["status"]
            }
            for v in self.vehicles
        ])
