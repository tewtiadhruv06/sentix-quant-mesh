import { Component } from '@angular/core';
import { QuantDashboardComponent } from './quant-dashboard/quant-dashboard.component';

@Component({
  selector: 'sentix-root',
  standalone: true,
  imports: [QuantDashboardComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'Sentix Quant Mesh';
}
