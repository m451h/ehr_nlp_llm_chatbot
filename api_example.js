/**
 * JavaScript API Client for EHR Chatbot
 * Example usage of the REST API endpoints
 * 
 * Base URL: http://localhost:8000
 */

const API_BASE_URL = 'http://localhost:8000';

// ============================================================================
// API Client Class
// ============================================================================

class EHRChatbotAPI {
    constructor(baseURL = API_BASE_URL) {
        this.baseURL = baseURL;
    }

    // Helper method for making requests
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || `HTTP error! status: ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    // GET /api/health
    async healthCheck() {
        return await this.request('/api/health');
    }

    // GET /api/conditions
    async getConditions() {
        return await this.request('/api/conditions');
    }

    // POST /api/chat/start
    async startChat(conditionId, clinicalData = null, generateEducationalNote = true) {
        return await this.request('/api/chat/start', {
            method: 'POST',
            body: JSON.stringify({
                condition_id: conditionId,
                clinical_data: clinicalData,
                generate_educational_note: generateEducationalNote
            })
        });
    }

    // POST /api/chat/query
    async queryChat(sessionId, query) {
        return await this.request('/api/chat/query', {
            method: 'POST',
            body: JSON.stringify({
                session_id: sessionId,
                query: query
            })
        });
    }

    // GET /api/chat/history/{session_id}
    async getChatHistory(sessionId) {
        return await this.request(`/api/chat/history/${sessionId}`);
    }

    // POST /api/chat/educational-note
    async generateEducationalNote(conditionId, clinicalData = null) {
        return await this.request('/api/chat/educational-note', {
            method: 'POST',
            body: JSON.stringify({
                condition_id: conditionId,
                clinical_data: clinicalData
            })
        });
    }

    // POST /api/chat/update-clinical-data
    async updateClinicalData(sessionId, clinicalData) {
        return await this.request('/api/chat/update-clinical-data', {
            method: 'POST',
            body: JSON.stringify({
                session_id: sessionId,
                clinical_data: clinicalData
            })
        });
    }

    // GET /api/stats/{session_id}
    async getStats(sessionId) {
        return await this.request(`/api/stats/${sessionId}`);
    }

    // DELETE /api/chat/session/{session_id}
    async deleteSession(sessionId) {
        return await this.request(`/api/chat/session/${sessionId}`, {
            method: 'DELETE'
        });
    }
}

// ============================================================================
// Usage Examples
// ============================================================================

async function exampleUsage() {
    const api = new EHRChatbotAPI();

    try {
        // 1. Check API health
        console.log('Checking API health...');
        const health = await api.healthCheck();
        console.log('Health:', health);

        // 2. Get available conditions
        console.log('\nGetting available conditions...');
        const conditionsResponse = await api.getConditions();
        console.log('Conditions:', conditionsResponse.conditions);

        // 3. Start a new chat session
        console.log('\nStarting new chat session...');
        const clinicalData = {
            age: '45 سال',
            gender: 'مرد',
            weight: '78 کیلوگرم',
            height: '175 سانتی‌متر',
            blood_pressure: '140/90 mmHg',
            fasting_blood_sugar: '95 mg/dL',
            cholesterol: '220 mg/dL',
            current_medications: 'متفورمین 500mg',
            medical_history: 'فشار خون بالا'
        };

        const startResponse = await api.startChat(
            'cond_type_2_diabetes', // condition_id
            clinicalData,
            true // generate educational note
        );
        console.log('Chat started:', startResponse);
        const sessionId = startResponse.session_id;

        // 4. Send a query
        console.log('\nSending query...');
        const queryResponse = await api.queryChat(
            sessionId,
            'چه غذاهایی برای دیابت خوبه؟'
        );
        console.log('Response:', queryResponse);

        // 5. Send another query
        console.log('\nSending another query...');
        const queryResponse2 = await api.queryChat(
            sessionId,
            'علائم دیابت چیه؟'
        );
        console.log('Response:', queryResponse2);

        // 6. Get chat history
        console.log('\nGetting chat history...');
        const history = await api.getChatHistory(sessionId);
        console.log('History:', history);

        // 7. Get statistics
        console.log('\nGetting statistics...');
        const stats = await api.getStats(sessionId);
        console.log('Stats:', stats);

        // 8. Generate educational note separately
        console.log('\nGenerating educational note...');
        const noteResponse = await api.generateEducationalNote(
            'cond_type_2_diabetes',
            clinicalData
        );
        console.log('Educational Note:', noteResponse.note);

    } catch (error) {
        console.error('Error:', error);
    }
}

// ============================================================================
// React/React Native Example Hook
// ============================================================================

function useEHRChatbot() {
    const [sessionId, setSessionId] = React.useState(null);
    const [messages, setMessages] = React.useState([]);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);
    const api = new EHRChatbotAPI();

    const startChat = async (conditionId, clinicalData) => {
        setLoading(true);
        setError(null);
        try {
            const response = await api.startChat(conditionId, clinicalData);
            setSessionId(response.session_id);
            setMessages([]);
            return response;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const sendMessage = async (query) => {
        if (!sessionId) {
            throw new Error('No active session. Start a chat first.');
        }

        setLoading(true);
        setError(null);
        
        try {
            // Add user message to UI immediately
            setMessages(prev => [...prev, {
                role: 'user',
                content: query
            }]);

            const response = await api.queryChat(sessionId, query);
            
            // Add bot response
            setMessages(prev => [...prev, {
                role: 'bot',
                content: response.message,
                confidence_level: response.confidence_level
            }]);

            return response;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const loadHistory = async () => {
        if (!sessionId) return;
        
        setLoading(true);
        try {
            const history = await api.getChatHistory(sessionId);
            setMessages(history.messages || []);
            return history;
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return {
        sessionId,
        messages,
        loading,
        error,
        startChat,
        sendMessage,
        loadHistory
    };
}

// ============================================================================
// Vue.js Example
// ============================================================================

const useEHRChatbotVue = () => {
    const sessionId = ref(null);
    const messages = ref([]);
    const loading = ref(false);
    const error = ref(null);
    const api = new EHRChatbotAPI();

    const startChat = async (conditionId, clinicalData) => {
        loading.value = true;
        error.value = null;
        try {
            const response = await api.startChat(conditionId, clinicalData);
            sessionId.value = response.session_id;
            messages.value = [];
            return response;
        } catch (err) {
            error.value = err.message;
            throw err;
        } finally {
            loading.value = false;
        }
    };

    const sendMessage = async (query) => {
        if (!sessionId.value) {
            throw new Error('No active session. Start a chat first.');
        }

        loading.value = true;
        error.value = null;
        
        try {
            messages.value.push({
                role: 'user',
                content: query
            });

            const response = await api.queryChat(sessionId.value, query);
            
            messages.value.push({
                role: 'bot',
                content: response.message,
                confidence_level: response.confidence_level
            });

            return response;
        } catch (err) {
            error.value = err.message;
            throw err;
        } finally {
            loading.value = false;
        }
    };

    return {
        sessionId,
        messages,
        loading,
        error,
        startChat,
        sendMessage
    };
};

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { EHRChatbotAPI, useEHRChatbot, useEHRChatbotVue };
}

// Run example if in browser console
if (typeof window !== 'undefined') {
    window.EHRChatbotAPI = EHRChatbotAPI;
    // Uncomment to run example:
    // exampleUsage();
}

