package ai.safenest.shared

import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.request.delete
import io.ktor.client.request.get
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.contentType

interface SafeNestApi {
    suspend fun register(req: RegisterRequest): TokenResponse
    suspend fun login(req: LoginRequest): TokenResponse
    suspend fun listChildren(): List<ChildResponse>
    suspend fun createChild(req: ChildCreateRequest): ChildResponse
    suspend fun createPairingCode(childId: Int): PairingCodeResponse
    suspend fun listAlerts(): List<ParentAlertResponse>
    suspend fun registerPushToken(req: RegisterPushTokenRequest): PushTokenResponse
    suspend fun revokePushToken(token: String)
}

internal class SafeNestApiImpl(private val client: HttpClient) : SafeNestApi {
    override suspend fun register(req: RegisterRequest): TokenResponse =
        client.post("/auth/register") { contentType(ContentType.Application.Json); setBody(req) }.body()

    override suspend fun login(req: LoginRequest): TokenResponse =
        client.post("/auth/login") { contentType(ContentType.Application.Json); setBody(req) }.body()

    override suspend fun listChildren(): List<ChildResponse> =
        client.get("/family/children").body()

    override suspend fun createChild(req: ChildCreateRequest): ChildResponse =
        client.post("/family/children") { contentType(ContentType.Application.Json); setBody(req) }.body()

    override suspend fun createPairingCode(childId: Int): PairingCodeResponse =
        client.post("/family/children/$childId/pairing-code").body()

    override suspend fun listAlerts(): List<ParentAlertResponse> =
        client.get("/family/alerts").body()

    override suspend fun registerPushToken(req: RegisterPushTokenRequest): PushTokenResponse =
        client.post("/family/push-tokens") { contentType(ContentType.Application.Json); setBody(req) }.body()

    override suspend fun revokePushToken(token: String) {
        client.delete("/family/push-tokens") {
            url { parameters.append("token", token) }
        }
    }
}

