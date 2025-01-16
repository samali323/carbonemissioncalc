"""ICAO emissions calculator implementation."""


class ICAOEmissionsCalculator:
    def __init__(self):
        # GCD correction factors - see section 4.2 of methodology
        self.GCD_CORRECTIONS = {
            "short": {"threshold": 550, "correction": 50},  # < 550 km
            "medium": {"threshold": 5500, "correction": 100},  # 550-5500 km
            "long": {"threshold": float('inf'), "correction": 125}  # > 5500 km
        }

        # Standard masses from methodology
        self.PASSENGER_MASS = 100  # kg per passenger including baggage
        self.EQUIPMENT_MASS = 50  # kg per seat equipment weight

        # Route group load factors from Appendix A
        self.ROUTE_GROUPS = {
            "INTRA_EUROPE": {
                "passenger_load_factor": 0.823,
                "passenger_to_cargo_factor": 0.9612,
                "description": "Flights within Europe"
            },
            "EUR_NAM": {
                "passenger_load_factor": 0.831,
                "passenger_to_cargo_factor": 0.7996,
                "description": "Europe - North America"
            },
            "DOMESTIC": {
                "passenger_load_factor": 0.791,
                "passenger_to_cargo_factor": 0.9335,
                "description": "Domestic flights"
            }
        }

        # Cabin class factors based on surface area ratios
        self.CABIN_FACTORS = {
            "economy": {
                "abreast_ratio": 1.0,  # baseline
                "pitch": 32,  # inches
                "yseat_factor": 1.0
            },
            "premium_economy": {
                "abreast_ratio": 1.2,
                "pitch": 38,
                "yseat_factor": 1.5
            },
            "business": {
                "abreast_ratio": 2.0,
                "pitch": 48,
                "yseat_factor": 2.0
            },
            "first": {
                "abreast_ratio": 2.2,
                "pitch": 60,
                "yseat_factor": 2.4
            }
        }

        # ICAO fuel consumption data by aircraft type and distance
        # Based on Appendix C tables
        self.FUEL_CONSUMPTION = {
            "A320": {
                125: 1672, 250: 3430, 500: 4585, 750: 6212,
                1000: 7772, 1500: 10766, 2000: 13648, 2500: 16452
            },
            "B737": {
                125: 1695, 250: 3439, 500: 4515, 750: 6053,
                1000: 7517, 1500: 10304, 2000: 12964, 2500: 15537
            }
            # Additional aircraft data from Appendix C would go here
        }

    def calculate_emissions(self,
                            distance_km: float,
                            aircraft_type: str,
                            cabin_class: str = "business",
                            route_group: str = "INTRA_EUROPE",
                            passengers: int = 30,
                            cargo_tons: float = 2.0,
                            is_international: bool = True) -> dict:
        """
        Calculate emissions using ICAO methodology

        Args:
            distance_km: Great Circle Distance in kilometers
            aircraft_type: Type of aircraft (e.g., "A320", "B737")
            cabin_class: Cabin class (economy, premium_economy, business, first)
            route_group: Route group for load factors
            passengers: Number of passengers
            cargo_tons: Cargo weight in metric tons
            is_international: Whether this is an international flight

        Returns:
            Dictionary containing emissions results
        """
        try:
            if distance_km < 200:  # Increased from 100 to 200
                if distance_km < 100:
                    base_fuel_consumption = distance_km * 3.5
                else:
                    # Gradual scaling for distances between 100-200km
                    base_fuel_consumption = distance_km * (3.5 + (distance_km - 100) * 0.02)

                emissions = base_fuel_consumption * 3.16
                total_emissions = emissions

                return {
                    "emissions_total_kg": total_emissions,
                    "emissions_per_pax_kg": total_emissions / passengers,
                    "fuel_consumption_kg": base_fuel_consumption,
                    "corrected_distance_km": distance_km,
                    "route_group": route_group,
                    "factors_applied": {
                        "short_distance_calculation": True,
                        "fuel_factor": 3.5,
                        "co2_factor": 3.16,
                        "is_international": is_international
                    }
                }
            # 1. Apply GCD correction factor
            corrected_distance = self._apply_gcd_correction(distance_km)

            # 2. Get route factors
            route_factors = self.ROUTE_GROUPS.get(route_group, self.ROUTE_GROUPS["INTRA_EUROPE"])
            pax_load_factor = route_factors["passenger_load_factor"]
            pax_cargo_factor = route_factors["passenger_to_cargo_factor"]

            # 3. Get cabin class factors
            cabin_info = self.CABIN_FACTORS[cabin_class.lower()]

            # Calculate Yseat factor using surface area method
            surface = cabin_info["abreast_ratio"] * cabin_info["pitch"]
            min_surface = self.CABIN_FACTORS["economy"]["abreast_ratio"] * self.CABIN_FACTORS["economy"]["pitch"]
            yseat_factor = surface / min_surface if min_surface > 0 else 1.0

            # 4. Calculate total mass (passengers + cargo)
            # Calculate passenger mass including equipment
            pax_mass = (passengers * self.PASSENGER_MASS +
                        passengers * self.EQUIPMENT_MASS) / 1000  # Convert to tons

            # Total mass including cargo
            total_mass = pax_mass + cargo_tons

            # Calculate passenger allocation factor
            pax_allocation = pax_mass / total_mass if total_mass > 0 else 1.0

            # 5. Calculate fuel consumption
            fuel_consumption = self._interpolate_fuel_consumption(
                aircraft_type,
                corrected_distance / 1.852  # Convert km to nautical miles
            )

            # Calculate total occupied Yseat
            total_seats = passengers / pax_load_factor if pax_load_factor > 0 else passengers
            total_yseat = total_seats * yseat_factor
            occupied_yseat = total_yseat * pax_load_factor

            # Calculate CO2 per passenger using ICAO formula
            co2_per_pax = ((fuel_consumption * pax_cargo_factor * pax_allocation) /
                           occupied_yseat) * yseat_factor * 3.16

            # Calculate total flight emissions
            total_emissions = co2_per_pax * passengers

            return {
                "emissions_total_kg": total_emissions,
                "emissions_per_pax_kg": co2_per_pax,
                "fuel_consumption_kg": fuel_consumption,
                "corrected_distance_km": corrected_distance,
                "route_group": route_group,
                "factors_applied": {
                    "pax_load_factor": pax_load_factor,
                    "pax_cargo_factor": pax_cargo_factor,
                    "yseat_factor": yseat_factor,
                    "gcd_correction": corrected_distance - distance_km,
                    "pax_allocation": pax_allocation,
                    "is_international": is_international
                }
            }

        except Exception as e:
            raise ValueError(f"Error calculating emissions: {str(e)}")

    def _apply_gcd_correction(self, distance_km: float) -> float:
        """Apply ICAO GCD corrections based on distance."""
        for category in ["short", "medium", "long"]:
            if distance_km <= self.GCD_CORRECTIONS[category]["threshold"]:
                return distance_km + self.GCD_CORRECTIONS[category]["correction"]
        return distance_km + self.GCD_CORRECTIONS["long"]["correction"]

    def _interpolate_fuel_consumption(self, aircraft: str, distance_nm: float) -> float:
        """
        Interpolate fuel consumption for given distance using ICAO fuel tables.

        Args:
            aircraft: Aircraft type
            distance_nm: Distance in nautical miles

        Returns:
            Interpolated fuel consumption in kg
        """
        if aircraft not in self.FUEL_CONSUMPTION:
            aircraft = "A320"  # Default to A320 if aircraft not found

        fuel_table = self.FUEL_CONSUMPTION[aircraft]
        distances = sorted(fuel_table.keys())

        # Handle edge cases
        if distance_nm <= distances[0]:
            return fuel_table[distances[0]]
        if distance_nm >= distances[-1]:
            return fuel_table[distances[-1]]

        # Find bracketing distances and interpolate
        for i in range(len(distances) - 1):
            if distances[i] <= distance_nm <= distances[i + 1]:
                d1, d2 = distances[i], distances[i + 1]
                f1, f2 = fuel_table[d1], fuel_table[d2]
                return f1 + (f2 - f1) * (distance_nm - d1) / (d2 - d1)

    def get_route_group_factors(self, origin: str, destination: str) -> dict:
        """Get load factors for a specific route."""
        # Determine route group based on origin/destination
        if origin[:2] == destination[:2]:
            return self.ROUTE_GROUPS["DOMESTIC"]
        elif origin[:2] in ["GB", "FR", "DE", "IT", "ES"] and \
                destination[:2] in ["GB", "FR", "DE", "IT", "ES"]:
            return self.ROUTE_GROUPS["INTRA_EUROPE"]
        else:
            return self.ROUTE_GROUPS["EUR_NAM"]
