class RegisterRequest {
  RegisterRequest({required this.email, required this.password});
  final String email;
  final String password;

  Map<String, dynamic> toJson() => {'email': email, 'password': password};
}

class LoginRequest {
  LoginRequest({required this.email, required this.password});
  final String email;
  final String password;

  Map<String, dynamic> toJson() => {'email': email, 'password': password};
}

class TokenResponse {
  TokenResponse({required this.accessToken, required this.tokenType});
  final String accessToken;
  final String tokenType;

  factory TokenResponse.fromJson(Map<String, dynamic> json) => TokenResponse(
        accessToken: (json['access_token'] ?? '').toString(),
        tokenType: (json['token_type'] ?? 'bearer').toString(),
      );
}

class MeResponse {
  MeResponse({required this.email, required this.role});
  final String email;
  final String role;

  factory MeResponse.fromJson(Map<String, dynamic> json) => MeResponse(
        email: (json['email'] ?? '').toString(),
        role: (json['role'] ?? '').toString(),
      );
}

