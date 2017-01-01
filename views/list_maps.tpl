
<html>
% include("head.tpl")
<body>
% include("update_button.tpl")
<table class="maps">
% for i in range(0, len(maps), 3):
<tr>
  <td>
<%
checked = maps[i]["id"] in subscribed
include("map.tpl", **maps[i], checked=checked)
%>
  </td>
  <td>
<%
if len(maps) > i+1:
  include("map.tpl", **maps[i+1], checked=maps[i+1]["id"] in subscribed)
end
%>
  </td>
  <td>
<%
if len(maps) > i+2:
  include("map.tpl", **maps[i+2],  checked=maps[i+2]["id"] in subscribed)
end
%>
  </td>
</tr>
% end
</table>
<body>
</html>