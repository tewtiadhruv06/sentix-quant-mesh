package com.sentix.quant.service;

import org.junit.jupiter.api.Test;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;
import static org.springframework.http.MediaType.APPLICATION_JSON;

class FmpDataServiceTest {

    @Test
    void searchTicker_shouldParseSymbolFromJsonArray() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        FmpDataService fmpDataService = new FmpDataService(builder.build(), "test-key");

        server.expect(requestTo("/api/v3/search?limit=1&apikey=test-key&query=tesla"))
                .andRespond(withSuccess("[{\"symbol\":\"TSLA\",\"name\":\"Tesla, Inc.\"}]", APPLICATION_JSON));

        assertThat(fmpDataService.searchTicker("tesla")).isEqualTo("TSLA");
        server.verify();
    }
}
