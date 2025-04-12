/*
 * Código Morse para Arduino com Relé - COMPLETAMENTE CORRIGIDO
 * Compatível com programa Python e usando lógica invertida para o relé
 */

// Pino do Relé (altere conforme necessário)
#define RELAY_PIN 8

// LED embutido para diagnóstico visual
#define LED_BUILTIN 13

// CORREÇÃO: Durações ajustadas para resolver o problema dos traços rápidos
int dot_duration = 200;      // duração do ponto em ms (CURTO)
int dash_duration = 600;     // duração do traço em ms (LONGO - 3x ponto) 
int symbol_space = 200;      // espaço entre elementos (igual ao ponto) 
int letter_space = 600;      // espaço entre letras (3x ponto)
int word_space = 1400;       // espaço entre palavras (7x ponto)

// Indica se está transmitindo
bool transmitting = false;

void setup() {
  // Inicializar porta serial
  Serial.begin(9600);
  
  // Configurar pino do Relé e LED interno
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LED_BUILTIN, OUTPUT);
  
  // Relé desligado inicialmente (lógica invertida)
  digitalWrite(RELAY_PIN, HIGH);
  digitalWrite(LED_BUILTIN, LOW);
  
  // Mostrar mensagem de inicialização
  Serial.println("Arduino Morse Code Ready - EMERGENCY FIX");
}

void loop() {
  // Verificar se há dados disponíveis
  if (Serial.available() > 0) {
    // Ler o primeiro byte (comando)
    char cmd = Serial.read();
    
    // Processar comando
    switch (cmd) {
      case 'T': // Comando de teste
        // Enviar "OK" exatamente como esperado
        Serial.print("OK");
        Serial.flush();
        blink_led(3);  // Piscar LED 3 vezes para confirmação visual
        break;
        
      case 'C': // Configuração de tempos
        parse_config();
        break;
        
      case 'M': // Transmitir morse
        transmit_morse();
        break;
        
      case 'S': // Parar transmissão
        transmitting = false;
        digitalWrite(RELAY_PIN, HIGH); // Garantir que relé está desligado
        digitalWrite(LED_BUILTIN, LOW);
        Serial.println("S OK");
        break;
        
      case 'X': // Desligar relé
        digitalWrite(RELAY_PIN, HIGH); // Relé desligado (lógica invertida)
        digitalWrite(LED_BUILTIN, LOW);
        Serial.println("X OK");
        break;
        
      case 'D': // Transmitir SOS diretamente (para teste)
        Serial.println("Transmitindo SOS direto");
        transmit_sos();
        Serial.println("SOS concluído");
        break;
        
      // Transmitir traços longos para verificar duração
      case 'L':
        Serial.println("Teste de traços longos (---)");
        for (int i = 0; i < 3; i++) {
          Serial.print("-");
          dash(); // Traço longo
          if (i < 2) delay(symbol_space);
        }
        Serial.println("\nFim do teste de traços");
        break;
        
      default:
        // Verificar se é texto para transmitir
        if (isAlphaNumeric(cmd) || cmd == ' ') {
          String text = String(cmd) + Serial.readStringUntil('\n');
          text.toUpperCase();
          Serial.print("Transmitindo texto: ");
          Serial.println(text);
          transmit_text(text);
          Serial.println("Transmissão concluída");
        }
        break;
    }
  }
}

// Função para transmitir SOS diretamente
void transmit_sos() {
  // S: ... (três pontos - CURTOS)
  Serial.println("S: pontos curtos (...)");
  for (int i = 0; i < 3; i++) {
    // Ponto - Sinal CURTO
    digitalWrite(RELAY_PIN, LOW);    // Relé ligado (lógica invertida)
    digitalWrite(LED_BUILTIN, HIGH); // LED para indicação visual
    delay(dot_duration);
    digitalWrite(RELAY_PIN, HIGH);   // Relé desligado
    digitalWrite(LED_BUILTIN, LOW);
    
    // Espaço entre símbolos (exceto após o último ponto)
    if (i < 2) {
      delay(symbol_space);
    }
  }
  
  // Espaço entre letras
  delay(letter_space);
  
  // O: --- (três traços - LONGOS)
  Serial.println("O: traços longos (---)");
  for (int i = 0; i < 3; i++) {
    // Traço - Sinal LONGO
    digitalWrite(RELAY_PIN, LOW);    // Relé ligado (lógica invertida)
    digitalWrite(LED_BUILTIN, HIGH); // LED para indicação visual
    delay(dash_duration);
    digitalWrite(RELAY_PIN, HIGH);   // Relé desligado
    digitalWrite(LED_BUILTIN, LOW);
    
    // Espaço entre símbolos (exceto após o último traço)
    if (i < 2) {
      delay(symbol_space);
    }
  }
  
  // Espaço entre letras
  delay(letter_space);
  
  // S: ... (três pontos - CURTOS)
  Serial.println("S: pontos curtos (...)");
  for (int i = 0; i < 3; i++) {
    // Ponto - Sinal CURTO
    digitalWrite(RELAY_PIN, LOW);    // Relé ligado (lógica invertida)
    digitalWrite(LED_BUILTIN, HIGH); // LED para indicação visual
    delay(dot_duration);
    digitalWrite(RELAY_PIN, HIGH);   // Relé desligado
    digitalWrite(LED_BUILTIN, LOW);
    
    // Espaço entre símbolos (exceto após o último ponto)
    if (i < 2) {
      delay(symbol_space);
    }
  }
}

// Função simples para transmitir um ponto (sinal CURTO)
void dot() {
  // VERIFICAÇÃO VISUAL PARA DEBUG
  Serial.print("[PONTO:");
  Serial.print(dot_duration);
  Serial.print("ms]");
  
  digitalWrite(RELAY_PIN, LOW);    // Relé ligado (lógica invertida)
  digitalWrite(LED_BUILTIN, HIGH); // LED ligado
  delay(dot_duration);             // Duração do ponto (CURTO)
  digitalWrite(RELAY_PIN, HIGH);   // Relé desligado
  digitalWrite(LED_BUILTIN, LOW);  // LED desligado
}

// Função simples para transmitir um traço (sinal LONGO)
void dash() {
  // VERIFICAÇÃO VISUAL PARA DEBUG
  Serial.print("[TRAÇO:");
  Serial.print(dash_duration);
  Serial.print("ms]");
  
  digitalWrite(RELAY_PIN, LOW);    // Relé ligado (lógica invertida)
  digitalWrite(LED_BUILTIN, HIGH); // LED ligado
  delay(dash_duration);            // Duração do traço (LONGO)
  digitalWrite(RELAY_PIN, HIGH);   // Relé desligado
  digitalWrite(LED_BUILTIN, LOW);  // LED desligado
}

// Função para piscar LED rapidamente (indicação visual)
void blink_led(int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(100);
    digitalWrite(LED_BUILTIN, LOW);
    delay(100);
  }
}

// Função para processar configuração de tempos
void parse_config() {
  // Formato esperado: C,dot_duration,dash_duration,symbol_space,letter_space,word_space\n
  String config = Serial.readStringUntil('\n');
  config.trim();
  
  Serial.print("Recebida configuração: ");
  Serial.println(config);
  
  // Extrair valores
  int values[5]; // Para armazenar os 5 valores
  int valueIndex = 0;
  int lastComma = 0;
  
  // Percorrer a string procurando vírgulas
  for (int i = 0; i < config.length() && valueIndex < 5; i++) {
    if (config.charAt(i) == ',') {
      // Extrair valor entre vírgulas
      String valueStr = config.substring(lastComma, i);
      values[valueIndex++] = valueStr.toInt();
      lastComma = i + 1;
    }
  }
  
  // Pegar o último valor (após a última vírgula)
  if (valueIndex < 5 && lastComma < config.length()) {
    String valueStr = config.substring(lastComma);
    values[valueIndex] = valueStr.toInt();
  }
  
  // Guardar valores anteriores para diagnóstico
  int old_dot = dot_duration;
  int old_dash = dash_duration;
  int old_symbol = symbol_space;
  
  // Atualizar variáveis se valores válidos
  if (valueIndex >= 4) {
    dot_duration = values[0] > 0 ? values[0] : dot_duration;
    dash_duration = values[1] > 0 ? values[1] : dash_duration;
    symbol_space = values[2] > 0 ? values[2] : symbol_space;
    letter_space = values[3] > 0 ? values[3] : letter_space;
    word_space = values[4] > 0 ? values[4] : word_space;
    
    // IMPORTANTE: Garantir que os valores estejam corretos
    if (dash_duration < dot_duration*2) {
      dash_duration = dot_duration * 3; // Ajuste de emergência: dash deve ser 3x dot
      Serial.println("CORREÇÃO AUTOMÁTICA: dash_duration ajustado para 3x dot_duration");
    }
    
    if (symbol_space < 1) {
      symbol_space = dot_duration; // Ajuste de emergência: symbol_space deve ser igual a dot
      Serial.println("CORREÇÃO AUTOMÁTICA: symbol_space ajustado para igual a dot_duration");
    }
    
    // Imprimir configurações atuais para debug
    Serial.print("Tempos atualizados - Ponto (CURTO): ");
    Serial.print(dot_duration);
    Serial.print("ms (antes: ");
    Serial.print(old_dot);
    Serial.print("ms), Traço (LONGO): ");
    Serial.print(dash_duration);
    Serial.print("ms (antes: ");
    Serial.print(old_dash);
    Serial.println("ms)");
    
    Serial.print("Espaço símbolo: ");
    Serial.print(symbol_space);
    Serial.print("ms (antes: ");
    Serial.print(old_symbol);
    Serial.print("ms), Espaço letra: ");
    Serial.print(letter_space);
    Serial.print("ms, Espaço palavra: ");
    Serial.println(word_space);
    
    Serial.println("Config OK");
  } else {
    Serial.println("Config inválida");
  }
}

// Estrutura para armazenar o código Morse de cada caractere
struct MorseCode {
  char character;
  const char* code;
};

// Tabela de código Morse
const MorseCode morseTable[] = {
  {'A', ".-"}, {'B', "-..."}, {'C', "-.-."}, {'D', "-.."}, {'E', "."},
  {'F', "..-."}, {'G', "--."}, {'H', "...."}, {'I', ".."}, {'J', ".---"},
  {'K', "-.-"}, {'L', ".-.."}, {'M', "--"}, {'N', "-."}, {'O', "---"},
  {'P', ".--."}, {'Q', "--.-"}, {'R', ".-."}, {'S', "..."}, {'T', "-"},
  {'U', "..-"}, {'V', "...-"}, {'W', ".--"}, {'X', "-..-"}, {'Y', "-.--"},
  {'Z', "--.."}, {'0', "-----"}, {'1', ".----"}, {'2', "..---"},
  {'3', "...--"}, {'4', "....-"}, {'5', "....."}, {'6', "-...."},
  {'7', "--..."}, {'8', "---.."}, {'9', "----."},
  {' ', " "}  // Espaço para separar palavras
};

// Função para transmitir código Morse
void transmit_morse() {
  // Formato esperado: M,código_morse\n
  String morse = Serial.readStringUntil('\n');
  morse.trim();
  
  Serial.print("Recebido para transmitir: [");
  Serial.print(morse);
  Serial.println("]");
  
  // Caso especial para SOS
  if (morse.equals("... --- ...")) {
    Serial.println("Detectado SOS - usando transmissão otimizada");
    transmit_sos();
    Serial.println("M OK");
    return;
  }
  
  // Verificar se há código para transmitir
  if (morse.length() > 0) {
    transmitting = true;
    
    // Dividir o código nas letras e palavras
    int i = 0;
    
    while (i < morse.length() && transmitting) {
      // Verificar comandos de parada
      if (Serial.available() > 0) {
        char cmd = Serial.read();
        if (cmd == 'S') {
          transmitting = false;
          digitalWrite(RELAY_PIN, HIGH); // Garantir que relé está desligado
          digitalWrite(LED_BUILTIN, LOW);
          Serial.println("Transmissão interrompida");
          break;
        }
      }
      
      char c = morse.charAt(i);
      
      // Processar símbolo
      if (c == '.') {
        // Ponto (CURTO)
        dot();
        
        // Verificar se o próximo caractere é parte da mesma letra
        if (i + 1 < morse.length() && morse.charAt(i + 1) != ' ') {
          delay(symbol_space);  // Espaço entre símbolos na mesma letra
        }
        i++;
      } 
      else if (c == '-') {
        // Traço (LONGO)
        dash();
        
        // Verificar se o próximo caractere é parte da mesma letra
        if (i + 1 < morse.length() && morse.charAt(i + 1) != ' ') {
          delay(symbol_space);  // Espaço entre símbolos na mesma letra
        }
        i++;
      } 
      else if (c == ' ') {
        // Contar espaços consecutivos para determinar o tipo de separação
        int count = 0;
        while (i < morse.length() && morse.charAt(i) == ' ') {
          count++;
          i++;
        }
        
        // Decidir o tipo de espaço baseado na quantidade
        if (count >= 3) {
          // Três ou mais espaços = separação entre palavras
          Serial.print("[ESPAÇO-PALAVRA:");
          Serial.print(word_space);
          Serial.print("ms]");
          delay(word_space);
        } 
        else if (count >= 1) {
          // Um ou dois espaços = separação entre letras
          Serial.print("[ESPAÇO-LETRA:");
          Serial.print(letter_space);
          Serial.print("ms]");
          delay(letter_space);
        }
      }
      else {
        // Caractere inválido, apenas pular
        i++;
      }
    }
    
    Serial.println(); 
    
    // Garantir que o relé está desligado no final
    digitalWrite(RELAY_PIN, HIGH);
    digitalWrite(LED_BUILTIN, LOW);
    
    // Confirmar conclusão
    if (transmitting) {
      Serial.println("M OK");
    }
    transmitting = false;
  } 
  else {
    Serial.println("Erro: código morse vazio");
  }
}

// Função para transmitir texto convertendo para Morse 
void transmit_text(String text) {
  transmitting = true;
  
  Serial.println("Transmitindo texto em Morse...");
  
  for (int i = 0; i < text.length() && transmitting; i++) {
    char c = text.charAt(i);
    
    // Procura o caractere na tabela Morse
    const char* morseChar = NULL;
    for (int j = 0; j < sizeof(morseTable) / sizeof(morseTable[0]); j++) {
      if (morseTable[j].character == c) {
        morseChar = morseTable[j].code;
        break;
      }
    }
    
    // Se o caractere foi encontrado na tabela
    if (morseChar != NULL) {
      Serial.print(c);
      Serial.print(": ");
      Serial.print(morseChar);
      Serial.print(" -> ");
      
      // Se for um espaço, aguarde o tempo entre palavras
      if (c == ' ') {
        Serial.print("[ESPAÇO-PALAVRA]");
        delay(word_space);
      }
      else {
        // Transmite cada elemento do código Morse (ponto ou traço)
        for (int k = 0; morseChar[k] != '\0' && transmitting; k++) {
          char element = morseChar[k];
          
          // Verificar comandos de parada
          if (Serial.available() > 0) {
            char cmd = Serial.read();
            if (cmd == 'S') {
              transmitting = false;
              digitalWrite(RELAY_PIN, HIGH);
              digitalWrite(LED_BUILTIN, LOW);
              Serial.println("Transmissão interrompida");
              break;
            }
          }
          
          // TRANSMITIR com as funções corretas
          if (element == '.') {
            dot();  // Ponto = sinal CURTO
          }
          else if (element == '-') {
            dash();  // Traço = sinal LONGO
          }
          
          // Pausa entre elementos se não for o último elemento do caractere
          if (morseChar[k+1] != '\0') {
            Serial.print("[ESPAÇO-SÍMBOLO]");
            delay(symbol_space);
          }
        }
        
        // Espaço entre letras (apenas se não for o último caractere e o próximo não for espaço)
        if (i < text.length() - 1 && text.charAt(i + 1) != ' ') {
          Serial.print("[ESPAÇO-LETRA]");
          delay(letter_space);
        }
      }
      
      Serial.println();
    }
  }
  
  // Garantir que o relé está desligado no final
  digitalWrite(RELAY_PIN, HIGH);
  digitalWrite(LED_BUILTIN, LOW);
  transmitting = false;
}