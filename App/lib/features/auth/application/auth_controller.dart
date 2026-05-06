import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/providers.dart';
import '../../../core/storage/secure_kv_store.dart';
import '../data/models.dart';
import '../domain/auth_state.dart';

final authControllerProvider = NotifierProvider<AuthController, AuthState>(AuthController.new);

class AuthController extends Notifier<AuthState> {
  late final SecureKvStore _store = ref.read(secureKvStoreProvider);

  @override
  AuthState build() {
    _bootstrap();
    return AuthState.initial;
  }

  Future<void> _bootstrap() async {
    final token = await _store.readToken();
    if (token == null || token.isEmpty) {
      state = state.copyWith(isLoading: false, token: null, role: null, email: null);
      return;
    }
    try {
      final me = await ref.read(apiClientProvider).me();
      state = state.copyWith(isLoading: false, token: token, role: me.role, email: me.email);
    } on ApiException {
      await _store.clearToken();
      state = state.copyWith(isLoading: false, token: null, role: null, email: null);
    }
  }

  Future<void> login({required String email, required String password}) async {
    state = state.copyWith(isLoading: true);
    try {
      final tokenRes = await ref.read(apiClientProvider).login(LoginRequest(email: email, password: password));
      await _store.writeToken(tokenRes.accessToken);
      final me = await ref.read(apiClientProvider).me();
      state = state.copyWith(isLoading: false, token: tokenRes.accessToken, role: me.role, email: me.email);
    } finally {
      state = state.copyWith(isLoading: false);
    }
  }

  Future<void> register({required String email, required String password}) async {
    state = state.copyWith(isLoading: true);
    try {
      final tokenRes = await ref.read(apiClientProvider).register(RegisterRequest(email: email, password: password));
      await _store.writeToken(tokenRes.accessToken);
      final me = await ref.read(apiClientProvider).me();
      state = state.copyWith(isLoading: false, token: tokenRes.accessToken, role: me.role, email: me.email);
    } finally {
      state = state.copyWith(isLoading: false);
    }
  }

  Future<void> logout() async {
    state = state.copyWith(isLoading: true);
    await _store.clearToken();
    state = state.copyWith(isLoading: false, token: null, role: null, email: null);
  }
}

