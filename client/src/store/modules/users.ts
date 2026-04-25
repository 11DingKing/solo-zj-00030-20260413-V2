import {
  Action,
  getModule,
  Module,
  Mutation,
  VuexModule
} from "vuex-module-decorators";
import { deleteUser, getUsers, updateUser, createUser, updateUserRoles, getUserRoles } from "@/api/users";
import store from "@/store";
import { IUserCreate, IUserData, IUserUpdate, IRoleData } from "@/api/types";

export interface IUsersState {
  users: IUserData[];
}

@Module({ dynamic: true, store, name: "users" })
class Users extends VuexModule implements IUsersState {
  public users: IUserData[] = [];

  @Mutation
  private SET_USERS(payload: IUserData[]) {
    this.users = payload;
  }

  @Mutation
  private SET_USER(payload: IUserData) {
    const users = this.users.filter(
      (user: IUserData) => user.id !== payload.id
    );
    users.push(payload);
    this.users = users;
  }

  @Mutation
  private DELETE_USER(id: number) {
    this.users = this.users.filter((user: IUserData) => user.id !== id);
  }

  @Action
  public async GetUsers(params: any) {
    const { data } = await getUsers(params);
    this.SET_USERS(data);
  }

  @Action
  public async CreateUser(createData: IUserCreate) {
    const { data } = await createUser(createData);
    this.SET_USER(data);
  }

  @Action
  public async UpdateUser(id: number, updateData: IUserUpdate) {
    const { data } = await updateUser(id, updateData);
    this.SET_USER(data);
  }

  @Action
  public async DeleteUser(id: number) {
    await deleteUser(id);
    this.DELETE_USER(id);
  }

  @Action
  public async UpdateUserRoles(payload: { userId: number; roleIds: number[] }) {
    const { data } = await updateUserRoles(payload.userId, payload.roleIds);
    this.UPDATE_USER_ROLES({ userId: payload.userId, roles: data });
  }

  @Action
  public async GetUserRoles(userId: number) {
    const { data } = await getUserRoles(userId);
    this.UPDATE_USER_ROLES({ userId, roles: data });
  }

  @Mutation
  private UPDATE_USER_ROLES(payload: { userId: number; roles: IRoleData[] }) {
    const users = this.users.map((user: IUserData) => {
      if (user.id === payload.userId) {
        return { ...user, roles: payload.roles };
      }
      return user;
    });
    this.users = users;
  }
}

export const UsersModule = getModule(Users);
