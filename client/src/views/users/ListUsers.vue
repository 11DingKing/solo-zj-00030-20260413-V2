<template>
  <div class="app-container">
    <el-button
      type="primary"
      icon="el-icon-circle-plus"
      size="medium"
      @click="$router.push('/users/create/')"
    >
      Add
    </el-button>

    <el-table
      v-loading="loading"
      :data="users"
      style="width: 100%"
      empty-text="-"
    >
      <el-table-column
        prop="id"
        label="ID"
        width="80"
      />
      <el-table-column
        prop="email"
        label="Email"
        width="300"
      />
      <el-table-column
        prop="first_name"
        label="First Name"
        min-width="100"
      />
      <el-table-column
        prop="last_name"
        label="Last Name"
        min-width="100"
      />

      <el-table-column
        label="Roles"
        prop="roles"
        min-width="150"
      >
        <template slot-scope="{row}">
          <el-tag
            v-for="role in row.roles"
            :key="role.id"
            type="primary"
            size="small"
            style="margin-right: 5px; margin-bottom: 5px;"
          >
            {{ role.name }}
          </el-tag>
          <span v-if="!row.roles || row.roles.length === 0" style="color: #909399;">
            No roles
          </span>
        </template>
      </el-table-column>

      <el-table-column
        label="Status"
        prop="status"
        min-width="100"
      >
        <template slot-scope="{row}">
          <el-tag
            v-if="row.status === 'active'"
            type="primary"
          >
            {{ row.status }}
          </el-tag>

          <el-tag
            v-else-if="row.status === 'disabled'"
            type="danger"
          >
            {{ row.status }}
          </el-tag>
          <el-tag
            v-else-if="row.status === 'inactive'"
            type="warning"
          >
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column
        prop="created_at"
        label="Created"
      >
        <template slot-scope="{row}">
          {{ new Date(row.created_at).toDateString() }}
        </template>
      </el-table-column>

      <el-table-column
        fixed="right"
        label="Actions"
        min-width="180px"
      >
        <template slot-scope="{row}">
          <el-button
            type="success"
            plain
            size="small"
            icon="el-icon-s-custom"
            @click="handleAssignRoles(row)"
          >
            Roles
          </el-button>

          <el-button
            type="primary"
            plain
            size="small"
            icon="el-icon-edit"
            @click="$router.push('/users/edit/' + row.id)"
          >
            Edit
          </el-button>

          <el-button
            type="danger"
            plain
            size="small"
            icon="el-icon-delete"
            @click="handleDeleteDialog(row)"
          >
            Delete
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      title="Assign Roles"
      :visible.sync="roleDialogVisible"
      width="40%"
    >
      <el-form label-width="120px">
        <el-form-item label="User">
          <span>{{ currentUser ? currentUser.email : '' }}</span>
        </el-form-item>
        <el-form-item label="Roles">
          <el-select
            v-model="selectedRoleIds"
            multiple
            placeholder="Select roles"
            style="width: 100%"
          >
            <el-option
              v-for="role in allRoles"
              :key="role.id"
              :label="role.name"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <span
        slot="footer"
        class="dialog-footer"
      >
        <el-button @click="roleDialogVisible = false">Cancel</el-button>
        <el-button
          type="primary"
          :loading="savingRoles"
          @click="saveUserRoles"
        >Save</el-button>
      </span>
    </el-dialog>

    <el-dialog
      title="Tips"
      :visible.sync="deleteDialogVisible"
      width="30%"
      :before-close="deleteData"
    >
      <span>Delete user?</span>
      <span
        slot="footer"
        class="dialog-footer"
      >
        <el-button @click="deleteDialogVisible = false">Cancel</el-button>
        <el-button
          type="primary"
          @click="deleteData()"
        >Confirm</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import { IUserData, IUserUpdate, IRoleData } from '@/api/types';
import { UsersModule } from '@/store/modules/users';
import { RolesModule } from '@/store/modules/roles';
import EditUser from './EditUser.vue';
import { UserStatus } from '@/api/enums';

@Component({
  name: 'ListUsers',
  components: {
    EditUser
  }
})
export default class extends Vue {
  private loading = true;
  private listQuery = { offset: 0, limit: 100 };
  private tempUserData = {} as IUserData;
  private deleteDialogVisible = false;
  private roleDialogVisible = false;
  private savingRoles = false;
  private currentUser: IUserData | null = null;
  private selectedRoleIds: number[] = [];

  get users() {
    return UsersModule.users;
  }

  get allRoles() {
    return RolesModule.roles;
  }

  get userStatus() {
    return UserStatus;
  }

  async created() {
    this.getUserList();
    await RolesModule.GetRoles({});
  }

  private resetTempArticleData() {
    this.tempUserData = {} as IUserData;
  }

  private async getUserList() {
    this.loading = true;
    await UsersModule.GetUsers(this.listQuery);
    this.loading = false;
  }

  private handleDeleteDialog(row: IUserData) {
    this.tempUserData = row;
    this.deleteDialogVisible = true;
  }

  private async deleteData() {
    await UsersModule.DeleteUser(this.tempUserData.id);
    this.deleteDialogVisible = false;
    this.resetTempArticleData();
  }

  private async updateData() {
    await UsersModule.UpdateUser(this.tempUserData.id, {});
  }

  private handleAssignRoles(user: IUserData) {
    this.currentUser = user;
    this.selectedRoleIds = (user.roles || []).map((r: IRoleData) => r.id);
    this.roleDialogVisible = true;
  }

  private async saveUserRoles() {
    if (!this.currentUser) return;
    
    this.savingRoles = true;
    try {
      await UsersModule.UpdateUserRoles({
        userId: this.currentUser.id,
        roleIds: this.selectedRoleIds
      });
      this.$message.success('Roles updated successfully');
      this.roleDialogVisible = false;
    } catch (error) {
      this.$message.error('Failed to update roles');
    } finally {
      this.savingRoles = false;
    }
  }
}
</script>

<style lang="scss" scoped>
  .el-header {
    padding-top: 20px;
    margin-top: auto
  }
</style>
