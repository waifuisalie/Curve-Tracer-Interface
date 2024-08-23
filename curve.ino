int i, j;
float pot0, pot1, VOLT, CORR, DV;

#define LED    13
#define PWMPin 6        

void setup() {
  Serial.begin(9600);
  pinMode(LED, OUTPUT);    
  pinMode(PWMPin, OUTPUT);
  analogReference(DEFAULT);
  analogWrite(PWMPin, 0);
  digitalWrite(LED, HIGH); // LED aceso indica início da coleta
}

void loop() {
  for (i = 5; i <= 255; i += 5) {
    analogWrite(PWMPin, i);  // Variando a tensão
    delay(10);
    
    // Leitura e média das leituras analog
    pot0 = 0;
    for (j = 0; j < 100; j++) {
      delay(1);
      pot0 += analogRead(0);   
    }  
    pot0 /= 100;  // Faz a média
     
    pot1 = 0;
    for (j = 0; j < 100; j++) {
      delay(1);
      pot1 += analogRead(1);
    }
    pot1 /= 100;
  
    DV = (pot0 - pot1);  // Calcula o diferencial de tensão
    
    // Calculando a corrente e tensão
    CORR = (5000 * pot1 / 1023) / 50;  // resistor de 50 ohms
    VOLT = (5.0 * DV / 1023);

    // Envia os dados para o Serial Monitor
    Serial.print(CORR);
    Serial.print(",");
    Serial.println(VOLT);
    
    delay(10);                   
  }
  
  digitalWrite(LED, LOW); // Desliga LED para indicar fim da coleta
  while(1); // Para o loop após a coleta dos dados
}
