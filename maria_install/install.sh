#!/bin/bash
dialog --title "MariaDB 安裝" --msgbox "歡迎使用 MariaDB 安裝腳本！" 10 40
dialog --title "MariaDB 安裝" --yesno "是否要繼續進行安裝？" 10 40
response=$?
if [ $response -eq 0 ]; then
    echo "繼續進行安裝"
else
    echo "安裝已取消"
    exit 1
fi

# 顯示下載進度條
(
    sudo apt update &> /dev/null
    echo "10"
    sudo apt install -y dialog mariadb-server &> /dev/null
    echo "80"
    sudo systemctl start mariadb
    sudo systemctl enable mariadb
    echo "100"
) | dialog --gauge "正在下載並安裝 MariaDB..." 10 70 0

# 安裝與初始化提示
dialog --title "MariaDB 安裝與初始化" --msgbox "MariaDB 已安裝並啟動成功，接下來將進行初始化設置。" 10 40

# 設定 MariaDB root 密碼
dialog --inputbox "請輸入 MariaDB root 密碼：" 10 40 2> root_password.txt
ROOT_PASSWORD=$(cat root_password.txt)
rm root_password.txt

# 設置 root 密碼
sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '$ROOT_PASSWORD';"

# 創建資料庫
dialog --inputbox "請輸入要創建的資料庫名稱：" 10 40 2> database_name.txt
DATABASE_NAME=$(cat database_name.txt)
rm database_name.txt
sudo mysql -uroot -p$ROOT_PASSWORD -e "CREATE DATABASE $DATABASE_NAME;"

# 創建資料表
dialog --inputbox "請輸入資料表名稱：" 10 40 2> table_name.txt
TABLE_NAME=$(cat table_name.txt)
rm table_name.txt
sudo mysql -uroot -p$ROOT_PASSWORD -e "USE $DATABASE_NAME; CREATE TABLE $TABLE_NAME (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(50), age INT);"

dialog --title "資料表建立完成" --msgbox "資料表 $TABLE_NAME 已成功建立，並包含欄位：id、name、age。" 10 40

# 顯示 CRUD 指令對照表
COMMAND_REF="指令對照表：
1. 新增資料:
   INSERT INTO $TABLE_NAME (name, age) VALUES ('your_name', your_age);
2. 讀取資料:
   SELECT * FROM $TABLE_NAME;
3. 更新資料:
   UPDATE $TABLE_NAME SET name='new_name', age=new_age WHERE id=target_id;
4. 刪除資料:
   DELETE FROM $TABLE_NAME WHERE id=target_id;
5. 自訂 SQL:
   輸入完整 SQL 指令進行操作。
"
dialog --msgbox "$COMMAND_REF" 15 60

# CRUD 操作迴圈
while true; do
  dialog --menu "請選擇 CRUD 操作：" 15 50 6 \
  1 "新增資料" \
  2 "讀取資料" \
  3 "更新資料" \
  4 "刪除資料" \
  5 "自訂 SQL 指令" \
  6 "退出" 2> choice.txt

  CHOICE=$(cat choice.txt)
  rm choice.txt

  case $CHOICE in
    1)
      # 新增資料操作
      dialog --msgbox "參考指令:
INSERT INTO $TABLE_NAME (name, age) VALUES ('your_name', your_age);" 10 60
      dialog --inputbox "請輸入名稱：" 10 40 2> name.txt
      NAME=$(cat name.txt)
      rm name.txt
      dialog --inputbox "請輸入年齡：" 10 40 2> age.txt
      AGE=$(cat age.txt)
      rm age.txt
      sudo mysql -uroot -p$ROOT_PASSWORD -e "USE $DATABASE_NAME; INSERT INTO $TABLE_NAME (name, age) VALUES ('$NAME', $AGE);"
      dialog --msgbox "新增成功！" 10 40
      ;;
    2)
      # 讀取資料操作
      dialog --msgbox "參考指令:
SELECT * FROM $TABLE_NAME;" 10 60
      RESULT=$(sudo mysql -uroot -p$ROOT_PASSWORD -e "USE $DATABASE_NAME; SELECT * FROM $TABLE_NAME;")
      dialog --title "讀取資料" --msgbox "$RESULT" 20 70
      ;;
    3)
      # 更新資料操作
      RESULT=$(sudo mysql -uroot -p$ROOT_PASSWORD -e "USE $DATABASE_NAME; SELECT * FROM $TABLE_NAME;")
      dialog --title "目前資料" --msgbox "$RESULT" 20 70
      dialog --msgbox "參考指令:
UPDATE $TABLE_NAME SET name='new_name', age=new_age WHERE id=target_id;" 10 60
      dialog --inputbox "請輸入要更新的 ID：" 10 40 2> update_id.txt
      UPDATE_ID=$(cat update_id.txt)
      rm update_id.txt
      dialog --inputbox "請輸入新名稱：" 10 40 2> new_name.txt
      NEW_NAME=$(cat new_name.txt)
      rm new_name.txt
      dialog --inputbox "請輸入新年齡：" 10 40 2> new_age.txt
      NEW_AGE=$(cat new_age.txt)
      rm new_age.txt
      sudo mysql -uroot -p$ROOT_PASSWORD -e "USE $DATABASE_NAME; UPDATE $TABLE_NAME SET name='$NEW_NAME', age=$NEW_AGE WHERE id=$UPDATE_ID;"
      dialog --msgbox "更新成功！" 10 40
      ;;
    4)
      # 刪除資料操作
      RESULT=$(sudo mysql -uroot -p$ROOT_PASSWORD -e "USE $DATABASE_NAME; SELECT * FROM $TABLE_NAME;")
      dialog --title "目前資料" --msgbox "$RESULT" 20 70
      dialog --msgbox "參考指令:
DELETE FROM $TABLE_NAME WHERE id=target_id;" 10 60
      dialog --inputbox "請輸入要刪除的 ID：" 10 40 2> delete_id.txt
      DELETE_ID=$(cat delete_id.txt)
      rm delete_id.txt
      sudo mysql -uroot -p$ROOT_PASSWORD -e "USE $DATABASE_NAME; DELETE FROM $TABLE_NAME WHERE id=$DELETE_ID;"
      dialog --msgbox "刪除成功！" 10 40
      ;;
    5)
      # 自訂 SQL 指令操作
      dialog --msgbox "您可以直接輸入完整的 SQL 指令，例如：
SELECT * FROM $TABLE_NAME;
或
UPDATE $TABLE_NAME SET name='xxx' WHERE id=1;" 12 60
      dialog --inputbox "請輸入 SQL 指令：" 10 60 2> custom_sql.txt
      CUSTOM_SQL=$(cat custom_sql.txt)
      rm custom_sql.txt
      sudo mysql -uroot -p$ROOT_PASSWORD -e "USE $DATABASE_NAME; $CUSTOM_SQL;"
      dialog --msgbox "SQL 指令已執行！" 10 40
      ;;
    6)
      dialog --msgbox "已退出 CRUD 操作。" 10 40
      break
      ;;
    *)
      dialog --msgbox "無效選擇，請重新操作。" 10 40
      ;;
  esac
done

# 清理
clear
echo "所有操作已完成，謝謝使用！"