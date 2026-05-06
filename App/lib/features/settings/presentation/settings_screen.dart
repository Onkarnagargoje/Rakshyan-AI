import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/providers.dart';

class SettingsRoute {
  static const location = '/settings';
  static final route = GoRoute(path: location, builder: (context, state) => const SettingsScreen());
}

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  late final TextEditingController _baseUrl;

  @override
  void initState() {
    super.initState();
    _baseUrl = TextEditingController(text: ref.read(appConfigProvider).apiBaseUrl);
  }

  @override
  void dispose() {
    _baseUrl.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    await ref.read(appConfigProvider).setApiBaseUrl(_baseUrl.text);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Saved. Restart the app to apply base URL.')));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 720),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Backend API', style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _baseUrl,
                      decoration: const InputDecoration(
                        labelText: 'API Base URL',
                        hintText: 'http://10.0.2.2:8000',
                      ),
                    ),
                    const SizedBox(height: 12),
                    Align(
                      alignment: Alignment.centerRight,
                      child: FilledButton.icon(onPressed: _save, icon: const Icon(Icons.save_outlined), label: const Text('Save')),
                    ),
                    const SizedBox(height: 8),
                    const Text('Tip: Android emulator uses http://10.0.2.2:8000 for localhost.'),
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

