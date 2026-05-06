package ai.safenest.shared

import io.ktor.client.HttpClient
import io.ktor.client.engine.okhttp.OkHttp
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.plugins.defaultRequest
import io.ktor.client.plugins.logging.LogLevel
import io.ktor.client.plugins.logging.Logger
import io.ktor.client.plugins.logging.Logging
import io.ktor.client.request.header
import io.ktor.http.HttpHeaders
import io.ktor.serialization.kotlinx.json.json
import kotlinx.serialization.json.Json

object ApiClient {
    // Android emulator: http://10.0.2.2:8000 ; physical device: your LAN IP.
    var baseUrl: String = "http://10.0.2.2:8000"

    fun createApi(tokenProvider: () -> String?): SafeNestApi {
        val client = HttpClient(OkHttp) {
            install(ContentNegotiation) {
                json(
                    Json {
                        ignoreUnknownKeys = true
                        isLenient = true
                    },
                )
            }
            install(Logging) {
                logger = object : Logger {
                    override fun log(message: String) {
                        // Keep stdout logs minimal; swap to Timber if desired.
                        kotlin.io.println(message)
                    }
                }
                level = LogLevel.INFO
            }
            defaultRequest {
                url(baseUrl)
                val tok = tokenProvider()
                if (!tok.isNullOrBlank()) {
                    header(HttpHeaders.Authorization, "Bearer $tok")
                }
                header(HttpHeaders.Accept, "application/json")
            }
        }
        return SafeNestApiImpl(client)
    }
}

