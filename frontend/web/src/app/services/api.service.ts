import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  getHealth(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`);
  }

  login(credentials: { username: str; password: str }): Observable<any> {
    return this.http.post(`${this.apiUrl}/auth/login`, credentials);
  }

  getPrediction(): Observable<any> {
    return this.http.get(`${this.apiUrl}/api/prediction`);
  }

  sendSensorData(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/sensor_data`, data);
  }
}
