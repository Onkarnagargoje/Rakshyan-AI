import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../data/models.dart';
import '../domain/logs_query.dart';

final logsProvider = FutureProvider.family<LogsResponse, LogsQuery>((ref, q) async {
  return ref.read(apiClientProvider).logs(analysisId: q.analysisId, limit: q.limit);
});

