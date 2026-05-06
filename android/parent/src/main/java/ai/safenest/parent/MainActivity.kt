package ai.safenest.parent

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import ai.safenest.shared.ApiClient
import ai.safenest.shared.LoginRequest
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            MaterialTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    var baseUrl by remember { mutableStateOf(ApiClient.baseUrl) }
                    var email by remember { mutableStateOf("parent@example.com") }
                    var password by remember { mutableStateOf("parent123") }
                    var token by remember { mutableStateOf<String?>(null) }
                    var status by remember { mutableStateOf("Not logged in") }

                    Column(
                        modifier = Modifier.fillMaxSize().padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                    ) {
                        Text("SafeNest Parent (MVP)", style = MaterialTheme.typography.titleLarge)
                        OutlinedTextField(value = baseUrl, onValueChange = { baseUrl = it }, label = { Text("API base URL") })
                        OutlinedTextField(value = email, onValueChange = { email = it }, label = { Text("Email") })
                        OutlinedTextField(value = password, onValueChange = { password = it }, label = { Text("Password") })

                        Button(onClick = {
                            ApiClient.baseUrl = baseUrl.trim()
                            val api = ApiClient.createApi { token }
                            status = "Logging in…"
                            CoroutineScope(Dispatchers.IO).launch {
                                try {
                                    val resp = api.login(LoginRequest(email.trim(), password))
                                    token = resp.accessToken
                                    status = "Logged in"
                                } catch (e: Exception) {
                                    status = "Login failed: ${e.message}"
                                }
                            }
                        }) { Text("Login") }

                        Text(status)
                    }
                }
            }
        }
    }
}

