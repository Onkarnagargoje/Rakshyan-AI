import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/widgets/async_value_view.dart';
import '../../analysis/application/analysis_controller.dart';
import '../../analysis/data/models.dart';
import '../../parent/presentation/parent_dashboard_screen.dart';
import '../../settings/presentation/settings_screen.dart';

class ChildDashboardRoute {
  static const location = '/child';
  static final route = GoRoute(path: location, builder: (context, state) => const ChildDashboardScreen());
}

class ChildDashboardScreen extends ConsumerStatefulWidget {
  const ChildDashboardScreen({super.key});

  @override
  ConsumerState<ChildDashboardScreen> createState() => _ChildDashboardScreenState();
}

class _ChildDashboardScreenState extends ConsumerState<ChildDashboardScreen> {
  final _chat = TextEditingController();
  AnalyzeChatRequest? _lastReq;

  @override
  void dispose() {
    _chat.dispose();
    super.dispose();
  }

  void _analyze() {
    final text = _chat.text.trim();
    if (text.isEmpty) return;
    setState(() {
      _lastReq = AnalyzeChatRequest(chatText: text);
    });
  }

  @override
  Widget build(BuildContext context) {
    final lastReq = _lastReq;
    final history = ref.watch(analysisHistoryProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Child Dashboard'),
        actions: [
          IconButton(onPressed: () => context.push(SettingsRoute.location), icon: const Icon(Icons.settings_outlined)),
          IconButton(onPressed: () => context.go(ParentDashboardRoute.location), icon: const Icon(Icons.family_restroom_outlined), tooltip: 'Parent view'),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _ChatCard(controller: _chat, onAnalyze: _analyze),
          const SizedBox(height: 12),
          if (lastReq != null)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: AsyncValueView(
                  value: ref.watch(analyzeChatProvider(lastReq)),
                  onRetry: _analyze,
                  data: (res) => _SafetyResult(res: res),
                ),
              ),
            ),
          const SizedBox(height: 12),
          _BadgesCard(history: history),
        ],
      ),
    );
  }
}

class _ChatCard extends StatelessWidget {
  const _ChatCard({required this.controller, required this.onAnalyze});
  final TextEditingController controller;
  final VoidCallback onAnalyze;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Chat input (simulated)', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            TextField(
              controller: controller,
              minLines: 3,
              maxLines: 8,
              decoration: const InputDecoration(
                hintText: 'Paste a chat snippet here…',
              ),
            ),
            const SizedBox(height: 12),
            Align(
              alignment: Alignment.centerRight,
              child: FilledButton.icon(onPressed: onAnalyze, icon: const Icon(Icons.shield_outlined), label: const Text('Analyze')),
            ),
          ],
        ),
      ),
    );
  }
}

class _SafetyResult extends StatelessWidget {
  const _SafetyResult({required this.res});
  final AnalyzeChatResponse res;

  @override
  Widget build(BuildContext context) {
    final score = _riskToScore(res.finalRiskLevel, res.finalConfidence);
    final color = _riskColor(context, res.finalRiskLevel);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(child: Text('Safety score', style: Theme.of(context).textTheme.titleMedium)),
            _RiskChip(level: res.finalRiskLevel),
          ],
        ),
        const SizedBox(height: 8),
        LinearProgressIndicator(value: score / 100.0, minHeight: 10, color: color),
        const SizedBox(height: 8),
        Text('$score / 100', style: Theme.of(context).textTheme.headlineSmall?.copyWith(color: color)),
        const SizedBox(height: 12),
        Text('Explainable AI', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        _ExplainPanel(res: res),
      ],
    );
  }
}

class _ExplainPanel extends StatelessWidget {
  const _ExplainPanel({required this.res});
  final AnalyzeChatResponse res;

  @override
  Widget build(BuildContext context) {
    final entries = res.agents.entries.toList()..sort((a, b) => a.key.compareTo(b.key));
    return ExpansionTile(
      tilePadding: EdgeInsets.zero,
      title: const Text('Agent outputs'),
      subtitle: Text('Supervisor + ${entries.length} agents'),
      children: [
        if (res.parentSummary != null && res.parentSummary!.trim().isNotEmpty)
          ListTile(
            title: const Text('Parent summary'),
            subtitle: Text(res.parentSummary!),
          ),
        ...entries.map(
          (e) => ListTile(
            title: Text(e.key),
            subtitle: Text(e.value.reason),
            trailing: _RiskChip(level: e.value.riskLevel),
          ),
        ),
      ],
    );
  }
}

class _BadgesCard extends StatelessWidget {
  const _BadgesCard({required this.history});
  final List<AnalyzeChatResponse> history;

  @override
  Widget build(BuildContext context) {
    final analyses = history.take(20).toList();
    final safeCount = analyses.where((a) => a.finalRiskLevel == 'low').length;
    final badges = <String>[
      if (analyses.isNotEmpty) 'First Check-in',
      if (safeCount >= 3) 'Safety Streak',
      if (analyses.length >= 5) 'Curious Explorer',
    ];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Badges', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            if (badges.isEmpty)
              const Text('Run a few analyses to unlock badges.')
            else
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: badges.map((b) => Chip(label: Text(b))).toList(),
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

int _riskToScore(String riskLevel, double confidence) {
  // Score is derived from backend outputs; no hardcoded risk values shown to user.
  final base = switch (riskLevel) {
    'low' => 90,
    'medium' => 60,
    'high' => 30,
    'critical' => 10,
    _ => 50,
  };
  final adj = ((confidence - 0.5) * 20).round(); // +/- 10
  final score = (base + adj).clamp(0, 100);
  return score;
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

