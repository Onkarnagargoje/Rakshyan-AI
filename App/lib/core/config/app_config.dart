import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AppConfig {
  AppConfig(this._prefs);

  final SharedPreferences _prefs;

  static const _kApiBaseUrl = 'api_base_url';

  /// Defaults:
  /// - Android emulator: http://10.0.2.2:8000
  /// - iOS simulator: http://127.0.0.1:8000
  /// - Physical device (demo): user should update in Settings.
  String get apiBaseUrl {
    final saved = _prefs.getString(_kApiBaseUrl);
    if (saved != null && saved.trim().isNotEmpty) return saved.trim();
    if (defaultTargetPlatform == TargetPlatform.android) return 'http://10.0.2.2:8000';
    return 'http://127.0.0.1:8000';
  }

  Future<void> setApiBaseUrl(String value) => _prefs.setString(_kApiBaseUrl, value.trim());
}

