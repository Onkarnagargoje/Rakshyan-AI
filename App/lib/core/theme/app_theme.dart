import 'package:flutter/material.dart';

class AppTheme {
  static ThemeData light() {
    final scheme = ColorScheme.fromSeed(seedColor: Colors.teal, brightness: Brightness.light);
    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      appBarTheme: AppBarTheme(backgroundColor: scheme.surface, foregroundColor: scheme.onSurface),
      inputDecorationTheme: const InputDecorationTheme(border: OutlineInputBorder()),
      snackBarTheme: SnackBarThemeData(backgroundColor: scheme.inverseSurface, contentTextStyle: TextStyle(color: scheme.onInverseSurface)),
      cardTheme: const CardThemeData(clipBehavior: Clip.antiAlias),
    );
  }

  static ThemeData dark() {
    final scheme = ColorScheme.fromSeed(seedColor: Colors.teal, brightness: Brightness.dark);
    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      appBarTheme: AppBarTheme(backgroundColor: scheme.surface, foregroundColor: scheme.onSurface),
      inputDecorationTheme: const InputDecorationTheme(border: OutlineInputBorder()),
      snackBarTheme: SnackBarThemeData(backgroundColor: scheme.inverseSurface, contentTextStyle: TextStyle(color: scheme.onInverseSurface)),
      cardTheme: const CardThemeData(clipBehavior: Clip.antiAlias),
    );
  }
}

