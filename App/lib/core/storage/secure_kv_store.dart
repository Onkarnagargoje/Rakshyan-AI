import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureKvStore {
  SecureKvStore(this._storage);

  final FlutterSecureStorage _storage;

  static const _kToken = 'auth_token';

  Future<String?> readToken() => _storage.read(key: _kToken);
  Future<void> writeToken(String token) => _storage.write(key: _kToken, value: token);
  Future<void> clearToken() => _storage.delete(key: _kToken);
}

