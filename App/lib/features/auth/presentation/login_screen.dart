import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/network/api_exception.dart';
import '../../child/presentation/child_dashboard_screen.dart';
import '../../settings/presentation/settings_screen.dart';
import '../application/auth_controller.dart';
import '../../admin/presentation/admin_dashboard_screen.dart';
import '../../parent/presentation/parent_dashboard_screen.dart';
import 'register_screen.dart';

class LoginRoute {
  static const location = '/login';
  static final route = GoRoute(path: location, builder: (context, state) => const LoginScreen());
}

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    final messenger = ScaffoldMessenger.of(context);
    try {
      await ref.read(authControllerProvider.notifier).login(email: _email.text.trim(), password: _password.text);
      if (!mounted) return;
      final auth = ref.read(authControllerProvider);
      final role = (auth.role ?? '').toLowerCase();
      if (role == 'admin') {
        context.go(AdminDashboardRoute.location);
      } else {
        context.go(ParentDashboardRoute.location);
      }
    } on ApiException catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(e.toString())));
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: Text(e.toString())));
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Sign in'),
        actions: [
          IconButton(onPressed: () => context.push(SettingsRoute.location), icon: const Icon(Icons.settings_outlined)),
        ],
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 520),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Form(
                  key: _formKey,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      TextFormField(
                        controller: _email,
                        decoration: const InputDecoration(labelText: 'Email'),
                        keyboardType: TextInputType.emailAddress,
                        autofillHints: const [AutofillHints.username, AutofillHints.email],
                        validator: (v) => (v == null || v.trim().isEmpty) ? 'Email is required' : null,
                      ),
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _password,
                        decoration: const InputDecoration(labelText: 'Password'),
                        obscureText: true,
                        autofillHints: const [AutofillHints.password],
                        validator: (v) => (v == null || v.length < 6) ? 'Min 6 characters' : null,
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        width: double.infinity,
                        child: FilledButton(
                          onPressed: auth.isLoading ? null : _submit,
                          child: auth.isLoading ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2)) : const Text('Sign in'),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          TextButton(onPressed: () => context.push(RegisterRoute.location), child: const Text('Create account')),
                          TextButton(
                            onPressed: () => context.go(ChildDashboardRoute.location),
                            child: const Text('Continue as Child (no login)'),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

