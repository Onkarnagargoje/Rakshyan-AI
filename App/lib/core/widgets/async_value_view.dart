import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AsyncValueView<T> extends StatelessWidget {
  const AsyncValueView({
    super.key,
    required this.value,
    required this.data,
    this.loading,
    this.errorTitle,
    this.onRetry,
  });

  final AsyncValue<T> value;
  final Widget Function(T) data;
  final Widget? loading;
  final String? errorTitle;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return value.when(
      data: data,
      loading: () => loading ?? const Center(child: CircularProgressIndicator()),
      error: (err, _) => _ErrorView(title: errorTitle ?? 'Something went wrong', message: err.toString(), onRetry: onRetry),
    );
  }
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.title, required this.message, required this.onRetry});
  final String title;
  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    final color = Theme.of(context).colorScheme;
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 520),
        child: Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 8),
                Text(message, style: TextStyle(color: color.onSurfaceVariant)),
                if (onRetry != null) ...[
                  const SizedBox(height: 12),
                  Align(
                    alignment: Alignment.centerRight,
                    child: FilledButton.icon(onPressed: onRetry, icon: const Icon(Icons.refresh), label: const Text('Retry')),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }
}

