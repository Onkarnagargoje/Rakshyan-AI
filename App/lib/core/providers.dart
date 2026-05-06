import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'config/app_config.dart';
import 'network/api_client.dart';
import 'network/auth_interceptor.dart';
import 'storage/secure_kv_store.dart';

final sharedPreferencesProvider = Provider<SharedPreferences>((ref) {
  throw UnimplementedError('sharedPreferencesProvider must be overridden');
});

final appConfigProvider = Provider<AppConfig>((ref) => AppConfig(ref.watch(sharedPreferencesProvider)));

final flutterSecureStorageProvider = Provider<FlutterSecureStorage>((ref) {
  return const FlutterSecureStorage();
});

final secureKvStoreProvider = Provider<SecureKvStore>((ref) {
  return SecureKvStore(ref.watch(flutterSecureStorageProvider));
});

final dioProvider = Provider<Dio>((ref) {
  final baseUrl = ref.watch(appConfigProvider).apiBaseUrl;
  final dio = Dio(BaseOptions(baseUrl: baseUrl, connectTimeout: const Duration(seconds: 10), receiveTimeout: const Duration(seconds: 20)));
  dio.interceptors.add(AuthInterceptor(ref.watch(secureKvStoreProvider)));
  return dio;
});

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient(ref.watch(dioProvider)));

