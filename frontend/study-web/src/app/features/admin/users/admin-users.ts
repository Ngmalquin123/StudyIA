import { Component, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { User } from '../../../core/auth/auth.models';
import { AuthService } from '../../../core/auth/auth.service';
import { apiErrorMessage } from '../../../core/http/api-error';
import { UsersService } from '../../../core/users/users.service';

@Component({
  selector: 'app-admin-users',
  imports: [DatePipe],
  templateUrl: './admin-users.html',
})
export class AdminUsers {
  private readonly usersService = inject(UsersService);
  protected readonly auth = inject(AuthService);

  protected readonly users = signal<User[]>([]);
  protected readonly total = signal(0);
  protected readonly loading = signal(true);
  protected readonly error = signal<string | null>(null);

  constructor() {
    this.load();
  }

  protected load(): void {
    this.loading.set(true);
    this.usersService.list().subscribe({
      next: (page) => {
        this.users.set(page.items);
        this.total.set(page.total);
        this.loading.set(false);
      },
      error: (error: unknown) => {
        this.error.set(apiErrorMessage(error, 'No se pudo cargar la lista'));
        this.loading.set(false);
      },
    });
  }

  protected toggleActive(user: User): void {
    this.error.set(null);
    this.usersService.update(user.id, { is_active: !user.is_active }).subscribe({
      next: (updated) =>
        this.users.update((list) => list.map((item) => (item.id === updated.id ? updated : item))),
      error: (error: unknown) => this.error.set(apiErrorMessage(error, 'No se pudo actualizar')),
    });
  }
}
