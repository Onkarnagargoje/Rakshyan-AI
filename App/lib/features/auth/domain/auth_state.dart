class AuthState {
  const AuthState({
    required this.isLoading,
    required this.token,
    required this.role,
    required this.email,
  });

  final bool isLoading;
  final String? token;
  final String? role;
  final String? email;

  bool get isAuthed => token != null && token!.isNotEmpty;

  AuthState copyWith({bool? isLoading, String? token, String? role, String? email}) {
    return AuthState(
      isLoading: isLoading ?? this.isLoading,
      token: token ?? this.token,
      role: role ?? this.role,
      email: email ?? this.email,
    );
  }

  static const initial = AuthState(isLoading: true, token: null, role: null, email: null);
}

