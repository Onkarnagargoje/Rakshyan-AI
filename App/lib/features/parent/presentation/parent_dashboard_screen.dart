import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../analysis/application/analysis_controller.dart';
import '../../analysis/data/models.dart';
import '../../auth/application/auth_controller.dart';
import '../../auth/presentation/login_screen.dart';
import '../../logs/presentation/logs_viewer_screen.dart';
import '../../settings/presentation/settings_screen.dart';

class ParentDashboardRoute {
  static const location = '/parent';
  static final route = GoRoute(path: location, builder: (context, state) => const ParentDashboardScreen());
}

class ParentDashboardScreen extends ConsumerWidget {
  const ParentDashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    final history = ref.watch(analysisHistoryProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Parent Dashboard'),
        actions: [
          IconButton(onPressed: () => context.push(SettingsRoute.location), icon: const Icon(Icons.settings_outlined)),
          IconButton(onPressed: () => context.push(LogsViewerRoute.location), icon: const Icon(Icons.receipt_long_outlined), tooltip: 'Logs'),
          PopupMenuButton<String>(
            onSelected: (v) async {
              if (v == 'logout') {
                await ref.read(authControllerProvider.notifier).logout();
                if (context.mounted) context.go(LoginRoute.location);
              }
            },
            itemBuilder: (context) => [
              if (auth.isAuthed) const PopupMenuItem(value: 'logout', child: Text('Logout')),
            ],
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _RiskOverviewCard(history: history),
          const SizedBox(height: 12),
          _RiskTrendCard(history: history),
          const SizedBox(height: 12),
          _AlertsCard(history: history),
        ],
      ),
    );
  }
}

class _RiskOverviewCard extends StatelessWidget {
  const _RiskOverviewCard({required this.history});
  final List<AnalyzeChatResponse> history;

  @override
  Widget build(BuildContext context) {
    final latest = history.isNotEmpty ? history.first : null;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Risk overview', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            if (latest == null)
              const Text('No analyses yet. Run a chat analysis from the Child dashboard.')
            else
              ListTile(
                contentPadding: EdgeInsets.zero,
                title: Text('Latest analysis #${latest.analysisId}'),
                subtitle: Text('Risk: ${latest.finalRiskLevel} • Confidence: ${(latest.finalConfidence * 100).toStringAsFixed(0)}%'),
                trailing: _RiskChip(level: latest.finalRiskLevel),
              ),
          ],
        ),
      ),
    );
  }
}

class _RiskTrendCard extends StatelessWidget {
  const _RiskTrendCard({required this.history});
  final List<AnalyzeChatResponse> history;

  @override
  Widget build(BuildContext context) {
    final points = history.take(30).toList().reversed.toList();
    final spots = <FlSpot>[];
    for (var i = 0; i < points.length; i++) {
      spots.add(FlSpot(i.toDouble(), _riskToTrendValue(points[i].finalRiskLevel)));
    }
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Risk trends', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            SizedBox(
              height: 180,
              child: spots.isEmpty
                  ? const Center(child: Text('No data yet'))
                  : LineChart(
                      LineChartData(
                        minY: 0,
                        maxY: 3,
                        gridData: const FlGridData(show: true),
                        titlesData: FlTitlesData(
                          leftTitles: AxisTitles(
                            sideTitles: SideTitles(
                              showTitles: true,
                              interval: 1,
                              getTitlesWidget: (value, _) => Text(_trendLabel(value.toInt())),
                            ),
                          ),
                          bottomTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                        ),
                        lineBarsData: [
                          LineChartBarData(
                            spots: spots,
                            isCurved: true,
                            barWidth: 3,
                            dotData: const FlDotData(show: false),
                          ),
                        ],
                      ),
                    ),
            ),
          ],
        ),
      ),
    );
  }
}

class _AlertsCard extends StatelessWidget {
  const _AlertsCard({required this.history});
  final List<AnalyzeChatResponse> history;

  @override
  Widget build(BuildContext context) {
    final alerts = history.where((h) => h.finalRiskLevel != 'low').take(10).toList();
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Alerts', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            if (alerts.isEmpty)
              const Text('No alerts yet.')
            else
              ...alerts.map(
                (a) => ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text('Analysis #${a.analysisId}'),
                  subtitle: Text('Risk: ${a.finalRiskLevel} • Confidence: ${(a.finalConfidence * 100).toStringAsFixed(0)}%'),
                  trailing: _RiskChip(level: a.finalRiskLevel),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _RiskChip extends StatelessWidget {
  const _RiskChip({required this.level});
  final String level;

  @override
  Widget build(BuildContext context) {
    final color = _riskColor(context, level);
    return Chip(
      label: Text(level.toUpperCase()),
      labelStyle: TextStyle(color: color),
      side: BorderSide(color: color),
      backgroundColor: color.withValues(alpha: 0.08),
    );
  }
}

double _riskToTrendValue(String riskLevel) {
  return switch (riskLevel) {
    'low' => 0,
    'medium' => 1,
    'high' => 2,
    'critical' => 3,
    _ => 1,
  };
}

String _trendLabel(int v) {
  return switch (v) { 0 => 'low', 1 => 'med', 2 => 'high', 3 => 'crit', _ => '' };
}

Color _riskColor(BuildContext context, String riskLevel) {
  final scheme = Theme.of(context).colorScheme;
  return switch (riskLevel) {
    'low' => scheme.tertiary,
    'medium' => Colors.orange,
    'high' => Colors.deepOrange,
    'critical' => scheme.error,
    _ => scheme.primary,
  };
}

