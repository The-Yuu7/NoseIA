import { Component, OnInit } from '@angular/core';
import { ApiService } from './services/api.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  title = 'Bio-E-Nose SCADA Dashboard (Angular)';
  isLoggedIn = false;
  loginUser = { username: 'admin', password: 'admin123' };
  loginError = '';
  currentUser: any = null;

  predictionData: any = {
    prediction: 'Esperando datos...',
    confidence: 0.0,
    ambient_status: 'AIRE AMBIENTE',
    latest_values: {
      MQ2: 23231.72, MQ4: 17268.26, MQ135: 12320.02, MQ3: 8474.87,
      MQ7: 7553.57, MQ9: 15570.25, temp: 22.51, humedad: 59.04
    }
  };

  constructor(private apiService: ApiService) {}

  ngOnInit(): void {
    this.checkHealth();
  }

  checkHealth(): void {
    this.apiService.getHealth().subscribe({
      next: (res) => console.log('API Status:', res),
      error: (err) => console.warn('API Offline:', err)
    });
  }

  onLogin(): void {
    this.loginError = '';
    this.apiService.login(this.loginUser).subscribe({
      next: (res) => {
        if (res.status === 'success') {
          this.isLoggedIn = true;
          this.currentUser = res.user;
          this.startPolling();
        }
      },
      error: (err) => {
        this.loginError = 'Credenciales de acceso inválidas. Intente con admin / admin123';
      }
    });
  }

  onLogout(): void {
    this.isLoggedIn = false;
    this.currentUser = null;
  }

  startPolling(): void {
    setInterval(() => {
      this.apiService.getPrediction().subscribe({
        next: (res) => {
          if (res) {
            this.predictionData = res;
          }
        },
        error: () => {}
      });
    }, 2000);
  }
}
