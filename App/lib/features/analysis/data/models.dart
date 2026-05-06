typedef RiskLevel = String; // "low" | "medium" | "high" | "critical"

class AnalyzeChatRequest {
  AnalyzeChatRequest({
    required this.chatText,
    this.platform = 'simulated',
    this.languageHint = 'auto',
    this.wearable,
    this.realtime = true,
  });

  final String platform;
  final String languageHint;
  final String chatText;
  final Map<String, dynamic>? wearable;
  final bool realtime;

  Map<String, dynamic> toJson() => {
        'platform': platform,
        'language_hint': languageHint,
        'chat_text': chatText,
        'wearable': wearable,
        'realtime': realtime,
      };
}

class AgentResult {
  AgentResult({
    required this.riskLevel,
    required this.confidence,
    required this.reason,
    required this.flags,
    required this.meta,
  });

  final RiskLevel riskLevel;
  final double confidence;
  final String reason;
  final List<String> flags;
  final Map<String, dynamic> meta;

  factory AgentResult.fromJson(Map<String, dynamic> json) => AgentResult(
        riskLevel: (json['risk_level'] ?? '').toString(),
        confidence: (json['confidence'] as num?)?.toDouble() ?? 0,
        reason: (json['reason'] ?? '').toString(),
        flags: (json['flags'] as List?)?.map((e) => e.toString()).toList() ?? const [],
        meta: (json['meta'] is Map) ? (json['meta'] as Map).map((k, v) => MapEntry(k.toString(), v)) : const {},
      );
}

class AgentHealth {
  AgentHealth({
    required this.agentName,
    required this.trustScore,
    this.lastLatencyMs,
    this.lastError,
    required this.lowConfidenceRate24h,
    required this.conflictRate24h,
  });

  final String agentName;
  final double trustScore;
  final int? lastLatencyMs;
  final String? lastError;
  final double lowConfidenceRate24h;
  final double conflictRate24h;

  factory AgentHealth.fromJson(Map<String, dynamic> json) => AgentHealth(
        agentName: (json['agent_name'] ?? '').toString(),
        trustScore: (json['trust_score'] as num?)?.toDouble() ?? 0,
        lastLatencyMs: (json['last_latency_ms'] as num?)?.toInt(),
        lastError: json['last_error']?.toString(),
        lowConfidenceRate24h: (json['low_confidence_rate_24h'] as num?)?.toDouble() ?? 0,
        conflictRate24h: (json['conflict_rate_24h'] as num?)?.toDouble() ?? 0,
      );
}

class MetaDiagnostics {
  MetaDiagnostics({
    required this.missingOutputs,
    required this.lowConfidence,
    required this.conflicts,
    required this.retries,
    required this.driftSuspected,
    required this.agentHealth,
  });

  final List<String> missingOutputs;
  final List<String> lowConfidence;
  final List<String> conflicts;
  final Map<String, int> retries;
  final List<String> driftSuspected;
  final List<AgentHealth> agentHealth;

  factory MetaDiagnostics.fromJson(Map<String, dynamic> json) => MetaDiagnostics(
        missingOutputs: (json['missing_outputs'] as List?)?.map((e) => e.toString()).toList() ?? const [],
        lowConfidence: (json['low_confidence'] as List?)?.map((e) => e.toString()).toList() ?? const [],
        conflicts: (json['conflicts'] as List?)?.map((e) => e.toString()).toList() ?? const [],
        retries: (json['retries'] is Map)
            ? (json['retries'] as Map).map((k, v) => MapEntry(k.toString(), (v as num?)?.toInt() ?? 0))
            : const {},
        driftSuspected: (json['drift_suspected'] as List?)?.map((e) => e.toString()).toList() ?? const [],
        agentHealth: (json['agent_health'] as List?)
                ?.whereType<Map>()
                .map((e) => AgentHealth.fromJson(e.map((k, v) => MapEntry(k.toString(), v))))
                .toList() ??
            const [],
      );
}

class AnalyzeChatResponse {
  AnalyzeChatResponse({
    required this.analysisId,
    required this.finalRiskLevel,
    required this.finalConfidence,
    required this.supervisor,
    required this.agents,
    required this.meta,
    this.parentSummary,
  });

  final int analysisId;
  final RiskLevel finalRiskLevel;
  final double finalConfidence;
  final Map<String, dynamic> supervisor;
  final Map<String, AgentResult> agents;
  final MetaDiagnostics meta;
  final String? parentSummary;

  factory AnalyzeChatResponse.fromJson(Map<String, dynamic> json) {
    final agentsJson = (json['agents'] is Map) ? (json['agents'] as Map) : const <dynamic, dynamic>{};
    return AnalyzeChatResponse(
      analysisId: (json['analysis_id'] as num?)?.toInt() ?? 0,
      finalRiskLevel: (json['final_risk_level'] ?? '').toString(),
      finalConfidence: (json['final_confidence'] as num?)?.toDouble() ?? 0,
      supervisor: (json['supervisor'] is Map) ? (json['supervisor'] as Map).map((k, v) => MapEntry(k.toString(), v)) : const {},
      agents: agentsJson.map((k, v) {
        final key = k.toString();
        final map = (v is Map) ? v.map((kk, vv) => MapEntry(kk.toString(), vv)) : <String, dynamic>{};
        return MapEntry(key, AgentResult.fromJson(map));
      }),
      meta: MetaDiagnostics.fromJson((json['meta'] is Map) ? (json['meta'] as Map).map((k, v) => MapEntry(k.toString(), v)) : const {}),
      parentSummary: json['parent_summary']?.toString(),
    );
  }
}

class RiskReportResponse {
  RiskReportResponse({
    required this.analysisId,
    required this.finalRiskLevel,
    required this.finalConfidence,
    required this.createdAt,
    required this.supervisor,
    required this.agents,
    required this.meta,
    required this.evidenceChain,
  });

  final int analysisId;
  final RiskLevel finalRiskLevel;
  final double finalConfidence;
  final String createdAt;
  final Map<String, dynamic> supervisor;
  final Map<String, AgentResult> agents;
  final MetaDiagnostics meta;
  final List<Map<String, dynamic>> evidenceChain;

  factory RiskReportResponse.fromJson(Map<String, dynamic> json) {
    final agentsJson = (json['agents'] is Map) ? (json['agents'] as Map) : const <dynamic, dynamic>{};
    return RiskReportResponse(
      analysisId: (json['analysis_id'] as num?)?.toInt() ?? 0,
      finalRiskLevel: (json['final_risk_level'] ?? '').toString(),
      finalConfidence: (json['final_confidence'] as num?)?.toDouble() ?? 0,
      createdAt: (json['created_at'] ?? '').toString(),
      supervisor: (json['supervisor'] is Map) ? (json['supervisor'] as Map).map((k, v) => MapEntry(k.toString(), v)) : const {},
      agents: agentsJson.map((k, v) {
        final key = k.toString();
        final map = (v is Map) ? v.map((kk, vv) => MapEntry(kk.toString(), vv)) : <String, dynamic>{};
        return MapEntry(key, AgentResult.fromJson(map));
      }),
      meta: MetaDiagnostics.fromJson((json['meta'] is Map) ? (json['meta'] as Map).map((k, v) => MapEntry(k.toString(), v)) : const {}),
      evidenceChain: (json['evidence_chain'] as List?)
              ?.whereType<Map>()
              .map((e) => e.map((k, v) => MapEntry(k.toString(), v)))
              .toList() ??
          const [],
    );
  }
}

