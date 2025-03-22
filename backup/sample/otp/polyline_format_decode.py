from polyline import decode

# Google encoded polyline string
encoded_polyline = "}anoEy~rtXe@g@s@k@gA}@kAkA{C{BWQcCkByAgAs@o@{BgBwAqAi@a@yA}AmAyA{AsBs@iAm@sACGc@iAQ]QUi@q@}AmBoA_ByAiBkBiCWSYUm@c@a@[c@[DKrBaDnAuBp@aAJKYY"

# Decode the encoded polyline
decoded_coordinates = decode(encoded_polyline)

# Print the decoded coordinates
print(decoded_coordinates)
