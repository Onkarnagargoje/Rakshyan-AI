import 'package:dio/dio.dart';

import '../network/api_exception.dart';
import '../../features/analysis/data/models.dart';
import '../../features/auth/data/models.dart';
import '../../features/agents/data/models.dart';
import '../../features/logs/data/models.dart';

class ApiClient {
  ApiClient(this._dio);
  final Dio _dio;

  // ---- Auth ----
  Future<TokenResponse> register(RegisterRequest payload) async {
    try {
      final res = await _dio.post('/auth/register', data: payload.toJson());
      return TokenResponse.fromJson(_asMap(res.data));
    } on DioException catch (e) {
      throw _toApiException(e);
    }
  }

  Future<TokenResponse> login(LoginRequest payload) async {
    try {
      final res = await _dio.post('/auth/login', data: payload.toJson());
      return TokenResponse.fromJson(_asMap(res.data));
    } on DioException catch (e) {
      throw _toApiException(e);
    }
  }

  Future<MeResponse> me() async {
    try {
      final res = await _dio.get('/auth/me');
      return MeResponse.fromJson(_asMap(res.data));
    } on DioException catch (e) {
      throw _toApiException(e);
    }
  }

  // ---- Analysis ----
  Future<AnalyzeChatResponse> analyzeChat(AnalyzeChatRequest payload) async {
    try {
      final res = await _dio.post('/analyze-chat', data: payload.toJson());
      return AnalyzeChatResponse.fromJson(_asMap(res.data));
    } on DioException catch (e) {
      throw _toApiException(e);
    }
  }

  Future<RiskReportResponse> getRiskReport(int analysisId) async {
    try {
      final res = await _dio.get('/get-risk-report/$analysisId');
      return RiskReportResponse.fromJson(_asMap(res.data));
    } on DioException catch (e) {
      throw _toApiException(e);
    }
  }

  // ---- Agents ----
  Future<AgentStatusResponse> agentStatus() async {
    try {
      final res = await _dio.get('/agent-status');
      return AgentStatusResponse.fromJson(_asMap(res.data));
    } on DioException catch (e) {
      throw _toApiException(e);
    }
  }

  // ---- Logs ----
  Future<LogsResponse> logs({int? analysisId, int limit = 200}) async {
    try {
      final res = await _dio.get(
        '/logs',
        queryParameters: {
          if (analysisId != null) 'analysis_id': analysisId,
          'limit': limit,
        },
      );
      return LogsResponse.fromJson(_asMap(res.data));
    } on DioException catch (e) {
      throw _toApiException(e);
    }
  }
}

Map<String, dynamic> _asMap(Object? value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return value.map((k, v) => MapEntry(k.toString(), v));
  throw ApiException('Unexpected response type');
}

ApiException _toApiException(DioException e) {
  final status = e.response?.statusCode;
  final data = e.response?.data;
  if (data is Map && data['detail'] is String) {
    return ApiException(data['detail'] as String, statusCode: status);
  }
  final msg = e.message ?? 'Network error';
  return ApiException(msg, statusCode: status);
}

