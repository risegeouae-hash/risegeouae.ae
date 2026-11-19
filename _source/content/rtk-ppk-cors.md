# What is RTK, PPK and CORS?

> **Quick answer:** RTK (real-time kinematic) corrects GNSS positions live using a base station or network, giving about 1 to 2 cm accuracy in the field. PPK (post-processed kinematic) applies the same corrections after the survey, in the office. CORS (continuously operating reference stations) are permanent base stations, often run by a national agency, that supply those corrections.

**RTK (real-time kinematic).** A GNSS rover receives correction data from a base station at a known point, by radio or mobile internet, and fixes its position to centimetre level within seconds. RTK is the standard method for topographic surveys, boundary setting-out and drone ground control. It needs a reliable correction link and works best within about 10 to 30 km of the base or inside a CORS network.

**PPK (post-processed kinematic).** The rover and base both log raw satellite data, and the corrections are applied later in software. PPK is common on survey drones, because it does not need a live link during the flight and can reduce the number of ground control points.

**CORS (continuously operating reference station).** A permanent GNSS station that records satellite data around the clock. A network of CORS lets surveyors work with a single rover and no base of their own ("network RTK"). Several national mapping and municipal agencies in the region run CORS networks.

| Term | When corrections are applied | Typical use |
| --- | --- | --- |
| RTK | Live, in the field | Topo surveys, stakeout, boundaries |
| PPK | After the survey, in software | Drone mapping, remote sites with no signal |
| CORS / network RTK | Live, from a permanent network | One-person surveys over a whole city or country |

**Related terms:** GNSS · Base station · PPP · Ground control point · Datum

**Find providers:** GNSS Receiver Dealers & Suppliers · Geodetic & GNSS Survey Services
