import '../../analysis/data/models.dart';

class AgentStatusResponse {
  AgentStatusResponse({required this.agents, required this.meta});

  final List<AgentHealth> agents;
  final Map<String, dynamic> meta;

  factory AgentStatusResponse.fromJson(Map<String, dynamic> json) => AgentStatusResponse(
        agents: (json['agents'] as List?)
                ?.whereType<Map>()
                .map((e) => AgentHealth.fromJson(e.map((k, v) => MapEntry(k.toString(), v))))
                .toList() ??
            const [],
        meta: (json['meta'] is Map) ? (json['meta'] as Map).map((k, v) => MapEntry(k.toString(), v)) : const {},
      );
}

