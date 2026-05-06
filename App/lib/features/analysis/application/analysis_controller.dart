import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../data/models.dart';

final analysisHistoryProvider = NotifierProvider<AnalysisHistoryController, List<AnalyzeChatResponse>>(AnalysisHistoryController.new);

class AnalysisHistoryController extends Notifier<List<AnalyzeChatResponse>> {
  @override
  List<AnalyzeChatResponse> build() => const [];

  void add(AnalyzeChatResponse item) => state = [item, ...state];
  void clear() => state = const [];
}

final analyzeChatProvider = FutureProvider.family<AnalyzeChatResponse, AnalyzeChatRequest>((ref, req) async {
  final res = await ref.read(apiClientProvider).analyzeChat(req);
  ref.read(analysisHistoryProvider.notifier).add(res);
  return res;
});

