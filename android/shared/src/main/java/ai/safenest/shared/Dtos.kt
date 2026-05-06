package ai.safenest.shared

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class TokenResponse(
    @SerialName("access_token") val accessToken: String,
)

@Serializable
data class RegisterRequest(
    val email: String,
    val password: String,
)

@Serializable
data class LoginRequest(
    val email: String,
    val password: String,
)

@Serializable
data class ChildCreateRequest(
    @SerialName("display_name") val displayName: String,
)

@Serializable
data class ChildResponse(
    val id: Int,
    @SerialName("display_name") val displayName: String,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class PairingCodeResponse(
    val code: String,
    @SerialName("child_id") val childId: Int,
    @SerialName("expires_at") val expiresAt: String,
)

@Serializable
data class LinkChildRequest(
    val code: String,
    @SerialName("device_label") val deviceLabel: String,
)

@Serializable
data class LinkChildResponse(
    @SerialName("child_id") val childId: Int,
    @SerialName("device_id") val deviceId: Int,
    @SerialName("ingest_token") val ingestToken: String,
    @SerialName("token_hint") val tokenHint: String,
)

@Serializable
data class ParentAlertResponse(
    val id: Int,
    @SerialName("child_id") val childId: Int,
    @SerialName("analysis_id") val analysisId: Int? = null,
    @SerialName("risk_level") val riskLevel: String,
    val title: String,
    val summary: String,
    @SerialName("read_at") val readAt: String? = null,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class RegisterPushTokenRequest(
    val provider: String = "fcm",
    val platform: String = "android",
    val token: String,
)

@Serializable
data class PushTokenResponse(
    val id: Int,
    val provider: String,
    val platform: String,
    @SerialName("created_at") val createdAt: String,
)

