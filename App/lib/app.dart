import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'core/theme/app_theme.dart';
import 'features/admin/presentation/admin_dashboard_screen.dart';
import 'features/auth/presentation/login_screen.dart';
import 'features/auth/presentation/register_screen.dart';
import 'features/auth/presentation/splash_screen.dart';
import 'features/child/presentation/child_dashboard_screen.dart';
import 'features/parent/presentation/parent_dashboard_screen.dart';
import 'features/settings/presentation/settings_screen.dart';

final _routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: SplashRoute.location,
    routes: [
      SplashRoute.route,
      LoginRoute.route,
      RegisterRoute.route,
      ChildDashboardRoute.route,
      ParentDashboardRoute.route,
      AdminDashboardRoute.route,
      SettingsRoute.route,
    ],
  );
});

class SafeNestApp extends ConsumerWidget {
  const SafeNestApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(_routerProvider);
    return MaterialApp.router(
      title: 'SafeNest AI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      themeMode: ThemeMode.system,
      routerConfig: router,
    );
  }
}

