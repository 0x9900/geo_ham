#! /usr/bin/env python3
# vim:fenc=utf-8
#
# Copyright © 2026 fred <github-fred@hidzz.com>
#
# Distributed under terms of the BSD 3-Clause license.

import math
import re
from dataclasses import dataclass
from typing import Tuple

__all__ = ["grid2rectangle", "grid2latlon", "latlon2grid", "distance", "azimuth", "ddm2decimal"]


LatLon = Tuple[float, float]

_GPS_RE = re.compile(r'([NS\-EW])(\d{2,3})\s+(\d+\.\d+)', re.IGNORECASE)

FIELD_LON_STEP = 20.0  # degrees
FIELD_LAT_STEP = 10.0  # degrees
SQUARE_LON_STEP = 2.0  # degrees
SQUARE_LAT_STEP = 1.0  # degrees

_A = 65  # ord('A')
_0 = 48  # ord('0')


@dataclass(frozen=True)
class Rectangle:
  lon_min: float
  lat_min: float
  lon_max: float
  lat_max: float


def grid2rectangle(maiden: str) -> Rectangle:
  """Convert a 4, 6, or 8 character Maidenhead locator to a rectangle.
  Returns a Rectangle(west, south, east, north) in decimal degrees
  """
  maiden = maiden.strip().upper()

  if len(maiden) not in (4, 6, 8):
    raise ValueError(
      f"grid2rectangle expects a 4-, 6-, or 8-character locator, "
      f"got {maiden!r} {len(maiden)} characters"
    )

  def _check_letters(a: str, b: str, hi: str, label: str) -> None:
    if not ("A" <= a <= hi and "A" <= b <= hi):
      raise ValueError(f"invalid Maidenhead {label}: {maiden!r}")

  def _check_digits(a: str, b: str, label: str) -> None:
    if not (a.isdigit() and b.isdigit()):
      raise ValueError(f"invalid Maidenhead {label}: {maiden!r}")

  # Field: AA-RR
  _check_letters(maiden[0], maiden[1], "R", "field")
  lon_min = (ord(maiden[0]) - _A) * FIELD_LON_STEP - 180.0
  lat_min = (ord(maiden[1]) - _A) * FIELD_LAT_STEP - 90.0

  # Square: 00-99
  _check_digits(maiden[2], maiden[3], "square")
  lon_min += (ord(maiden[2]) - _0) * SQUARE_LON_STEP
  lat_min += (ord(maiden[3]) - _0) * SQUARE_LAT_STEP

  lon_step = SQUARE_LON_STEP
  lat_step = SQUARE_LAT_STEP

  if len(maiden) >= 6:
    # Subsquare: AA-XX
    _check_letters(maiden[4], maiden[5], "X", "subsquare")
    lon_step /= 24.0
    lat_step /= 24.0
    lon_min += (ord(maiden[4]) - _A) * lon_step
    lat_min += (ord(maiden[5]) - _A) * lat_step

  if len(maiden) == 8:
    # Extended square: 00-99
    _check_digits(maiden[6], maiden[7], "extended square")
    lon_step /= 10.0
    lat_step /= 10.0
    lon_min += (ord(maiden[6]) - _0) * lon_step
    lat_min += (ord(maiden[7]) - _0) * lat_step

  return Rectangle(lon_min, lat_min, lon_min + lon_step, lat_min + lat_step)


def grid2latlon(maiden: str, center: bool = False) -> LatLon:
  """
  Optimized version converting maidenhead grid square locators (QRA)
  into a lat long tuple.
  """

  maiden = maiden.strip().upper()
  n = len(maiden)
  if n not in (2, 4, 6, 8):
    raise ValueError('Locator length error: 2, 4, 6 or 8 characters accepted')

  lon = (ord(maiden[0]) - _A) * FIELD_LON_STEP - 180.0
  lat = (ord(maiden[1]) - _A) * FIELD_LAT_STEP - 90.0
  if n == 2:
    return (lat + 5.0, lon + 10.0) if center else (lat, lon)

  lon += (ord(maiden[2]) - _0) * SQUARE_LON_STEP
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


def latlon2grid(lat: float, lon: float, precision: int = 6) -> str:
  """
  Convert (lat, lon) to a Maidenhead locator (QRA).
  precision: 2, 4, 6, or 8 characters.
  """
  lon += 180.0
  lat += 90.0

  # Field (A-R)
  lon_f, lon = divmod(lon, FIELD_LON_STEP)
  lat_f, lat = divmod(lat, FIELD_LAT_STEP)
  grid = chr(_A + int(lon_f)) + chr(_A + int(lat_f))
  if precision == 2:
    return grid

  # Square (0-9)
  lon_s, lon = divmod(lon, SQUARE_LON_STEP)
  lat_s, lat = divmod(lat, SQUARE_LAT_STEP)
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


def distance(orig: LatLon, dest: LatLon) -> float:
  """Calculate the great-circle distance between 2 coordinates (Haversine, in km)."""
  lat1, lon1 = orig
  lat2, lon2 = dest

  phi1 = math.radians(lat1)
  phi2 = math.radians(lat2)
  dphi = phi2 - phi1
  dlambda = math.radians(lon2 - lon1)

  a = math.sin(dphi * 0.5) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda * 0.5) ** 2
  return 2 * 6371.0 * math.asin(math.sqrt(a))


def azimuth(orig: LatLon, dest: LatLon) -> float:
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


def ddm2decimal(dms: str) -> float:
  """Parse a QRZ-style DDM coordinate string (e.g. 'N043 12.345') to decimal degrees."""
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
