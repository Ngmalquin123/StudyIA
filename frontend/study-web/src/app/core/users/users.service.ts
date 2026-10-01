import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { User } from '../auth/auth.models';

export interface UserList {
  total: number;
  items: User[];
}

export interface UserUpdate {
  name?: string;
  email?: string;
  password?: string;
  current_password?: string;
  rol?: string;
  is_active?: boolean;
}

@Injectable({ providedIn: 'root' })
export class UsersService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl}/users`;

  list(skip = 0, limit = 50): Observable<UserList> {
    return this.http.get<UserList>(this.api, { params: { skip, limit } });
  }

  update(id: number, data: UserUpdate): Observable<User> {
    return this.http.patch<User>(`${this.api}/${id}`, data);
  }
}
