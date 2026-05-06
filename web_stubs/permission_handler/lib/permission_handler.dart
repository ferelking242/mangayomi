library permission_handler;

import 'package:flutter/foundation.dart';

enum PermissionStatus {
  denied,
  granted,
  restricted,
  limited,
  permanentlyDenied,
  provisional,
}

extension PermissionStatusCheck on PermissionStatus {
  bool get isGranted => this == PermissionStatus.granted;
  bool get isDenied => this == PermissionStatus.denied;
  bool get isPermanentlyDenied => this == PermissionStatus.permanentlyDenied;
  bool get isRestricted => this == PermissionStatus.restricted;
  bool get isLimited => this == PermissionStatus.limited;
  bool get isProvisional => this == PermissionStatus.provisional;
}

class Permission {
  final String _name;
  const Permission._(this._name);

  static const Permission notification = Permission._('notification');
  static const Permission storage = Permission._('storage');
  static const Permission manageExternalStorage = Permission._('manageExternalStorage');
  static const Permission requestInstallPackages = Permission._('requestInstallPackages');
  static const Permission microphone = Permission._('microphone');
  static const Permission camera = Permission._('camera');
  static const Permission location = Permission._('location');
  static const Permission phone = Permission._('phone');
  static const Permission contacts = Permission._('contacts');
  static const Permission calendar = Permission._('calendar');
  static const Permission photos = Permission._('photos');
  static const Permission mediaLibrary = Permission._('mediaLibrary');
  static const Permission bluetooth = Permission._('bluetooth');
  static const Permission bluetoothScan = Permission._('bluetoothScan');
  static const Permission bluetoothConnect = Permission._('bluetoothConnect');
  static const Permission scheduleExactAlarm = Permission._('scheduleExactAlarm');
  static const Permission accessMediaLocation = Permission._('accessMediaLocation');
  static const Permission activityRecognition = Permission._('activityRecognition');
  static const Permission audio = Permission._('audio');
  static const Permission calendarFullAccess = Permission._('calendarFullAccess');
  static const Permission calendarWriteOnly = Permission._('calendarWriteOnly');
  static const Permission ignoreBatteryOptimizations = Permission._('ignoreBatteryOptimizations');
  static const Permission locationAlways = Permission._('locationAlways');
  static const Permission locationWhenInUse = Permission._('locationWhenInUse');
  static const Permission manageExternalStorageWithoutCache = Permission._('manageExternalStorageWithoutCache');
  static const Permission nearbyWifiDevices = Permission._('nearbyWifiDevices');
  static const Permission systemAlertWindow = Permission._('systemAlertWindow');
  static const Permission videos = Permission._('videos');

  // On web (kIsWeb == true): permissions are not applicable, always report as
  // granted so the app can continue without blocking on dialogs.
  //
  // On native platforms where this stub is compiled in via dependency_overrides:
  // - status / isGranted → denied  (correct initial state: not yet requested)
  // - request()          → granted (simulate user tapping "Allow" since the real
  //                                 plugin dialog is unavailable in this context)
  //
  // This fixes the bug where the onboarding screen showed all 3 permissions as
  // already granted on Android before the user had tapped anything.
  PermissionStatus get status =>
      kIsWeb ? PermissionStatus.granted : PermissionStatus.denied;
  bool get isGranted => kIsWeb;
  bool get isDenied => !kIsWeb;
  bool get isPermanentlyDenied => false;
  // request() always returns granted: on web nothing to request, on native the
  // stub simulates the user accepting the dialog (no real OS dialog available).
  PermissionStatus request() => PermissionStatus.granted;
}

Future<Map<Permission, PermissionStatus>> requestList(
    List<Permission> permissions) async =>
    {for (final p in permissions) p: PermissionStatus.granted};

Future<void> openAppSettings() async {}
