import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/widgets/async_value_view.dart';
import '../../auth/application/auth_controller.dart';
import '../../auth/presentation/login_screen.dart';
import '../../logs/presentation/logs_viewer_screen.dart';
import '../../settings/presentation/settings_screen.dart';
import '../providers/agent_status_provider.dart';

class AdminDashboardRoute {
  static const location = '/admin';
  static final route = GoRoute(path: location, builder: (context, state) => const AdminDashboardScreen());
}

class AdminDashboardScreen extends ConsumerWidget {
  const AdminDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final status = ref.watch(agentStatusProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Admin Dashboard'),
        actions: [
          IconButton(onPressed: () => context.push(SettingsRoute.location), icon: const Icon(Icons.settings_outlined)),
          IconButton(onPressed: () => context.push(LogsViewerRoute.location), icon: const Icon(Icons.receipt_long_outlined), tooltip: 'Logs'),
          IconButton(
            tooltip: 'Refresh',
            onPressed: () => ref.invalidate(agentStatusProvider),
            icon: const Icon(Icons.refresh),
          ),
          PopupMenuButton<String>(
            onSelected: (v) async {
              if (v == 'logout') {
                await ref.read(authControllerProvider.notifier).logout();
                if (context.mounted) context.go(LoginRoute.location);
              }
            },
            itemBuilder: (context) => const [
              PopupMenuItem(value: 'logout', child: Text('Logout')),
            ],
          ),
        ],
      ),
      body: AsyncValueView(
        value: status,
        onRetry: () => ref.invalidate(agentStatusProvider),
        data: (data) {
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Agent health', style: Theme.of(context).textTheme.titleMedium),
                      const SizedBox(height: 8),
                      ...data.agents.map(
                        (a) => ListTile(
                          title: Text(a.agentName),
                          subtitle: Text(
                            'Trust ${(a.trustScore * 100).toStringAsFixed(0)}% • '
                            'Low-conf ${(a.lowConfidenceRate24h * 100).toStringAsFixed(0)}% • '
                            'Conflicts ${(a.conflictRate24h * 100).toStringAsFixed(0)}%'
                            '${a.lastLatencyMs == null ? '' : ' • ${a.lastLatencyMs}ms'}',
                          ),
                          trailing: a.lastError == null
                              ? const Icon(Icons.check_circle_outline)
                              : Tooltip(message: a.lastError!, child: const Icon(Icons.error_outline)),
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text('Meta: ${data.meta}', style: Theme.of(context).textTheme.bodySmall),
                    ],
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

