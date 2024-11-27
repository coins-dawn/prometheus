.PHONY: download-data
download-data:
	./script/download_data.sh

.PHONY: convert-network
convert-network:
	./script/convert.sh

.PHONY: run-otp-server
run-otp-server:
	./script/run_otp_sever.sh
