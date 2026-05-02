# IDEA INTERLOCK MATRIX (NT24 §6)

Every idea must connect to at least 1 other idea.

```yaml
ideas:
  NT19_long_kinh:
    cuts_with: [NT24_cvp, NT26_anonymous, NT29_wallet]
  NT20_distrust:
    cuts_with: [NT22_triangle, NT24_2way, NT15_pyramid]
  NT21_oc_vit:
    cuts_with: [NT20_distrust, NT28_two_pass]
  NT22_triangle:
    cuts_with: [NT15_pyramid, NT20_distrust, NT14_3role]
  NT23_khach_la_thanh:
    cuts_with: [NT24_cvp, NT19_long_kinh]
  NT24_cvp:
    cuts_with: [NT23_khach_la_thanh, NT19_long_kinh, NT20_distrust]
  NT26_anonymous:
    cuts_with: [NT19_long_kinh, NT25_role_hijack]
  NT28_two_pass:
    cuts_with: [NT21_oc_vit, NT14_3role]
```
