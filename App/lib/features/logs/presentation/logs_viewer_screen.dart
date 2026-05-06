import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/widgets/async_value_view.dart';
import '../domain/logs_query.dart';
import '../providers/logs_provider.dart';

class LogsViewerRoute {
  static const location = '/logs';
  static final route = GoRoute(path: location, builder: (context, state) => const LogsViewerScreen());
}

class LogsViewerScreen extends ConsumerStatefulWidget {
  const LogsViewerScreen({super.key});

  @override
  ConsumerState<LogsViewerScreen> createState() => _LogsViewerScreenState();
}

class _LogsViewerScreenState extends ConsumerState<LogsViewerScreen> {
  final _analysisId = TextEditingController();
  int? _analysisIdValue;
  int _limit = 200;

  @override
  void dispose() {
    _analysisId.dispose();
    super.dispose();
  }

  void _apply() {
    setState(() {
      final raw = _analysisId.text.trim();
      _analysisIdValue = raw.isEmpty ? null : int.tryParse(raw);
    });
    ref.invalidate(logsProvider(LogsQuery(analysisId: _analysisIdValue, limit: _limit)));
  }

  @override
  Widget build(BuildContext context) {
    final query = LogsQuery(analysisId: _analysisIdValue, limit: _limit);
    final logs = ref.watch(logsProvider(query));
    return Scaffold(
      appBar: AppBar(
        title: const Text('Logs'),
        actions: [
          IconButton(onPressed: _apply, icon: const Icon(Icons.refresh)),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _analysisId,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(labelText: 'analysis_id (optional)'),
                  ),
                ),
                const SizedBox(width: 12),
                SizedBox(
                  width: 160,
                  child: DropdownButtonFormField<int>(
                    initialValue: _limit,
                    items: const [
                      DropdownMenuItem(value: 50, child: Text('50')),
                      DropdownMenuItem(value: 100, child: Text('100')),
                      DropdownMenuItem(value: 200, child: Text('200')),
                      DropdownMenuItem(value: 500, child: Text('500')),
                    ],
                    onChanged: (v) => setState(() => _limit = v ?? 200),
                    decoration: const InputDecoration(labelText: 'Limit'),
                  ),
                ),
                const SizedBox(width: 12),
                FilledButton.icon(onPressed: _apply, icon: const Icon(Icons.filter_alt_outlined), label: const Text('Apply')),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: AsyncValueView(
              value: logs,
              onRetry: () => ref.invalidate(logsProvider(query)),
              data: (data) {
                return ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: data.items.length,
                  separatorBuilder: (_, __) => const Divider(height: 1),
                  itemBuilder: (context, index) {
                    final item = data.items[index];
                    final title = (item['event'] ?? item['type'] ?? 'log').toString();
                    final ts = (item['created_at'] ?? item['timestamp'] ?? '').toString();
                    final analysisId = (item['analysis_id'] ?? '').toString();
                    return ListTile(
                      title: Text(title),
                      subtitle: Text([if (ts.isNotEmpty) ts, if (analysisId.isNotEmpty) 'analysis_id=$analysisId'].join(' • ')),
                      onTap: () => showDialog(
                        context: context,
                        builder: (_) => AlertDialog(
                          title: const Text('Log item'),
                          content: SingleChildScrollView(child: Text(item.toString())),
                          actions: [TextButton(onPressed: () => context.pop(), child: const Text('Close'))],
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

