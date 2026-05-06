import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../application/auth_controller.dart';
import '../../admin/presentation/admin_dashboard_screen.dart';
import '../../child/presentation/child_dashboard_screen.dart';
import '../../parent/presentation/parent_dashboard_screen.dart';
import 'login_screen.dart';

class SplashRoute {
  static const location = '/';
  static final route = GoRoute(
    path: location,
    builder: (context, state) => const SplashScreen(),
  );
}

class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _routeNext());
  }

  void _routeNext() {
    final auth = ref.read(authControllerProvider);
    if (auth.isLoading) {
      ref.listenManual(authControllerProvider, (_, __) => _routeNext());
      return;
    }
    if (!auth.isAuthed) {
      context.go(LoginRoute.location);
      return;
    }
    final role = (auth.role ?? '').toLowerCase();
    if (role == 'admin') {
      context.go(AdminDashboardRoute.location);
    } else if (role == 'parent') {
      context.go(ParentDashboardRoute.location);
    } else {
      context.go(ChildDashboardRoute.location);
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = Theme.of(context).colorScheme;
    return Scaffold(
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 520),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('SafeNest AI', style: Theme.of(context).textTheme.headlineSmall),
                    const SizedBox(height: 6),
                    Text('Child Cyber Safety Platform', style: TextStyle(color: color.onSurfaceVariant)),
                    const SizedBox(height: 16),
                    const LinearProgressIndicator(),
                    const SizedBox(height: 8),
                    Text('Connecting to your SafeNest backend…', style: TextStyle(color: color.onSurfaceVariant)),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

