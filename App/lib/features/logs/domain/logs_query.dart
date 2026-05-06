class LogsQuery {
  const LogsQuery({required this.analysisId, required this.limit});
  final int? analysisId;
  final int limit;

  @override
  bool operator ==(Object other) => other is LogsQuery && other.analysisId == analysisId && other.limit == limit;

  @override
  int get hashCode => Object.hash(analysisId, limit);
}

