#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2026 fred <github-fred@hidzz.com>
#
# Distributed under terms of the BSD 3-Clause license.

import math
import re

__all__ = ["grid2latlon", "latlon2grid", "distance", "azimuth", "dm2decimal"]

_A = 65  # ord('A')
_0 = 48  # ord('0')

_GPS_RE = re.compile(r'([NS\-EW])(\d{2,3})\s+(\d+\.\d+)', re.IGNORECASE)

def grid2latlon(maiden: str, center: bool = False) -> tuple[float, float]:
  """
  Optimized version converting maidenhead grid square locators (QRA)
  into a lat long tuple.
  """

  maiden = maiden.strip().upper()
  n = len(maiden)
  if n not in (2, 4, 6, 8):
    raise ValueError('Locator length error: 2, 4, 6 or 8 characters accepted')

  lon = (ord(maiden[0]) - _A) * 20 - 180.0
  lat = (ord(maiden[1]) - _A) * 10 - 90.0
  if n == 2:
    return (lat + 5.0, lon + 10.0) if center else (lat, lon)

  lon += (ord(maiden[2]) - _0) * 2
  lat += ord(maiden[3]) - _0
  if n == 4:
    return (lat + 0.5, lon + 1.0) if center else (lat, lon)

  lon += (ord(maiden[4]) - _A) * 0.08333333333333333
  lat += (ord(maiden[5]) - _A) * 0.041666666666666664
  if n == 6:
    return (lat + 0.020833333333333332, lon + 0.041666666666666664) if center else (lat, lon)

  lon += (ord(maiden[6]) - _0) * 0.008333333333333333
  lat += (ord(maiden[7]) - _0) * 0.004166666666666667
  return (lat + 0.002083333333333333, lon + 0.004166666666666667) if center else (lat, lon)


def latlon2grid(lat: double, lon: double, precision: int = 6) -> str:
  """
  Convert (lat, lon) to a Maidenhead locator (QRA).
  precision: 2, 4, 6, or 8 characters.
  """
  lon += 180.0
  lat += 90.0

  # Field (A-R)
  lon_f, lon = divmod(lon, 20.0)
  lat_f, lat = divmod(lat, 10.0)
  grid = chr(_A + int(lon_f)) + chr(_A + int(lat_f))
  if precision == 2:
    return grid

  # Square (0-9)
  lon_s, lon = divmod(lon, 2.0)
  lat_s, lat = divmod(lat, 1.0)
  grid += str(int(lon_s)) + str(int(lat_s))
  if precision == 4:
    return grid

  # Subsquare (a-x) — traditionally lowercase
  lon *= 60.0
  lat *= 60.0
  lon_sub, lon = divmod(lon, 5.0)
  lat_sub, lat = divmod(lat, 2.5)
  grid += chr(_A + int(lon_sub) + 32) + chr(_A + int(lat_sub) + 32)
  if precision == 6:
    return grid

  # Extended square (0-9)
  lon_e = int(lon / 5.0 * 10)
  lat_e = int(lat / 2.5 * 10)
  grid += str(lon_e) + str(lat_e)
  return grid


def distance(orig: tuple[float, float], dest: tuple[float, float]) -> float:
  """Calculate the great-circle distance between 2 coordinates (Haversine, in km)."""
  lat1, lon1 = orig
  lat2, lon2 = dest

  phi1 = math.radians(lat1)
  phi2 = math.radians(lat2)
  dphi = phi2 - phi1
  dlambda = math.radians(lon2 - lon1)

  a = math.sin(dphi * 0.5) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda * 0.5) ** 2
  return 2 * 6371.0 * math.asin(math.sqrt(a))


def azimuth(orig: tuple[float, float], dest: tuple[float, float]) -> float:
  """Calculate the compass bearing (0-360°) of `dest` from `orig`."""
  # pylint: disable=too-many-locals

  lat1, lon1 = orig
  lat2, lon2 = dest

  phi1 = math.radians(lat1)
  phi2 = math.radians(lat2)
  dlambda = math.radians(lon2 - lon1)

  sin_phi1, cos_phi1 = math.sin(phi1), math.cos(phi1)
  sin_phi2, cos_phi2 = math.sin(phi2), math.cos(phi2)
  sin_dl, cos_dl = math.sin(dlambda), math.cos(dlambda)

  x = cos_phi2 * sin_dl
  y = cos_phi1 * sin_phi2 - sin_phi1 * cos_phi2 * cos_dl

  return math.degrees(math.atan2(x, y)) % 360


def dm2decimal(dms):
  """Parse a QRZ-style DMS coordinate string (e.g. 'N043 12.345') to decimal degrees."""
  if not isinstance(dms, str):
    return dms

  match = _GPS_RE.match(dms)
  if not match:
    raise ValueError(f'Unrecognized GPS coordinate format: {dms!r}')

  direction, degrees, minutes = match.groups()
  result = int(degrees) + float(minutes) / 60

  if direction.lower() in ('s', 'w', '-'):
    result = -result

  return result
