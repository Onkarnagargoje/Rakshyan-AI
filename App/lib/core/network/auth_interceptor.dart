import 'package:dio/dio.dart';

import '../storage/secure_kv_store.dart';

class AuthInterceptor extends Interceptor {
  AuthInterceptor(this._store);
  final SecureKvStore _store;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    try {
      final token = await _store.readToken();
      if (token != null && token.isNotEmpty) {
        options.headers['Authorization'] = 'Bearer $token';
      }
    } catch (_) {
      // If secure storage is unavailable, continue without auth.
    }
    handler.next(options);
  }
}

