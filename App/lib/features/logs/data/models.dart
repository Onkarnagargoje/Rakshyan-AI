class LogsResponse {
  LogsResponse({required this.items});
  final List<Map<String, dynamic>> items;

  factory LogsResponse.fromJson(Map<String, dynamic> json) => LogsResponse(
        items: (json['items'] as List?)
                ?.whereType<Map>()
                .map((e) => e.map((k, v) => MapEntry(k.toString(), v)))
                .toList() ??
            const [],
      );
}

