import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../../agents/data/models.dart';

final agentStatusProvider = FutureProvider<AgentStatusResponse>((ref) async {
  return ref.read(apiClientProvider).agentStatus();
});

